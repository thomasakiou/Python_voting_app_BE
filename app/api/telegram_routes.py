import logging
import threading
import time
import requests
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from ..core import database, oauth2
from ..core.config import settings
from ..core.audit import record_audit_log
from ..core.otp_utils import normalize_nigerian_phone, send_otp_telegram
from ..domain import user as user_models

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{settings.api_prefix}/telegram", tags=["Telegram Bot"])


class TelegramTestSendRequest(BaseModel):
    username: str
    message: Optional[str] = "This is a test notification from the NECO MCS Electronic Voting System."


# ============================================================
# HELPER: Normalize phone digits for matching
# ============================================================
def _extract_last_10_digits(phone: str) -> str | None:
    """Extract the last 10 significant digits from a phone number for matching."""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(digits) < 10:
        return None
    return digits[-10:]


# ============================================================
# CORE MESSAGE HANDLER (Webhook + Polling)
# ============================================================
def handle_telegram_incoming_message(message: dict, db: Session):
    """
    Phone-number-only linking system.
    Supports:
      1. Tapping "Share My Phone Number" button (Telegram Contact).
      2. Typing phone number directly in chat (e.g. 07069244957 or 7069244957).
      3. /start - Shows instructions & contact button.
      4. /status - Checks current link status.
    All matching normalizes both 07069244957 and 7069244957 to the same 10-digit suffix.
    """
    if not message:
        return

    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    text = (message.get("text") or "").strip()
    from_user = message.get("from", {})
    tg_username = from_user.get("username") or from_user.get("first_name", "Member")

    bot_token = getattr(settings, "telegram_bot_token", None)

    def reply_tg(reply_text: str, reply_markup: dict = None):
        if not bot_token:
            logger.info(f"[SIMULATED TG REPLY to {chat_id}]: {reply_text}")
            return
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Error sending Telegram reply: {e}")

    # ── 1. CONTACT SHARING (Only verified native Telegram Contact Card accepted) ──
    contact = message.get("contact")
    if contact and contact.get("phone_number"):
        # Security Verification: Ensure the contact belongs to the sender's own Telegram account
        contact_user_id = contact.get("user_id")
        sender_id = from_user.get("id")
        if contact_user_id and sender_id and str(contact_user_id) != str(sender_id):
            reply_tg(
                "🚫 *Security Alert: Impersonation Blocked*\n\n"
                "You can only share your *own* phone number directly from your active Telegram app.\n\n"
                "Please tap the *'📱 Share My Phone Number'* button below.",
                reply_markup={
                    "keyboard": [[{"text": "📱 Share My Phone Number", "request_contact": True}]],
                    "resize_keyboard": True,
                    "one_time_keyboard": True,
                },
            )
            logger.warning(f"[Telegram Security] Impersonation attempt: Sender {sender_id} shared contact of user {contact_user_id}")
            return

        raw_phone = contact.get("phone_number")
        shared_suffix = _extract_last_10_digits(raw_phone)
        if not shared_suffix:
            reply_tg(
                "❌ *Invalid Phone Number*\n\n"
                "The phone number shared from Telegram could not be processed. Please try again.",
                reply_markup={"remove_keyboard": True},
            )
            return

        # 1. Match voter by phone number (matches 07069244957, 7069244957, +2347069244957)
        matched_voter = (
            db.query(user_models.User)
            .filter(user_models.User.phone.like(f"%{shared_suffix}"))
            .first()
        )
        if not matched_voter:
            all_voters = db.query(user_models.User).filter(user_models.User.phone.isnot(None)).all()
            for v in all_voters:
                if _extract_last_10_digits(v.phone) == shared_suffix:
                    matched_voter = v
                    break

        if not matched_voter:
            clean_display = raw_phone.strip()
            reply_tg(
                f"❌ *Phone Number Not Registered*\n\n"
                f"The phone number `{clean_display}` (suffix `{shared_suffix}`) does not match any registered voter in the NECO MCS Electoral System.\n\n"
                f"⚠️ Only registered voters with matching phone numbers on the official voters roll can link their accounts.\n\n"
                f"If you believe this is an error, please contact the Electoral Committee (ELECO).",
                reply_markup={"remove_keyboard": True},
            )
            logger.warning(f"[Telegram] Phone '{raw_phone}' (suffix {shared_suffix}) not found. chat_id={chat_id}")
            return

        # 2. Check if this voter is ALREADY linked to this EXACT chat_id
        if matched_voter.telegram_chat_id == chat_id:
            reply_tg(
                f"✅ *Already Connected!*\n\n"
                f"Hello *{matched_voter.full_name}*,\n"
                f"Your Telegram is already securely linked to your Voter ID: *{matched_voter.username}*.\n"
                f"Registered Phone: `{matched_voter.phone}`\n\n"
                f"You will receive all Election OTPs and notifications right here.",
                reply_markup={"remove_keyboard": True},
            )
            return

        # 3. Check if this voter is already linked to a DIFFERENT Telegram account
        if matched_voter.telegram_chat_id and matched_voter.telegram_chat_id != chat_id:
            reply_tg(
                f"🚫 *Account Already Linked*\n\n"
                f"Voter profile *{matched_voter.full_name}* (MCS: `{matched_voter.username}`) is already linked to another Telegram account.\n\n"
                f"Each voter can only link their Telegram once. Please contact the Electoral Committee (ELECO) if you need to update your registered account.",
                reply_markup={"remove_keyboard": True},
            )
            logger.warning(f"[Telegram] Voter '{matched_voter.username}' already linked to chat {matched_voter.telegram_chat_id}")
            return

        # 4. Check if this Telegram chat is already linked to a DIFFERENT voter
        other_voter = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .filter(user_models.User.id != matched_voter.id)
            .first()
        )
        if other_voter:
            reply_tg(
                f"⚠️ *Telegram Account Already In Use*\n\n"
                f"This Telegram account is currently linked to another voter (*{other_voter.full_name}*, MCS: `{other_voter.username}`).\n\n"
                f"Each Telegram account can only be used by one voter.",
                reply_markup={"remove_keyboard": True},
            )
            return

        # 5. Successfully Link!
        matched_voter.telegram_chat_id = chat_id
        matched_voter.telegram_username = f"@{tg_username}" if not tg_username.startswith("@") else tg_username
        db.commit()

        reply_tg(
            f"✅ *Phone Number Verified & Linked!*\n\n"
            f"Hello *{matched_voter.full_name}*,\n"
            f"Your Telegram account has been linked to your NECO MCS Voter ID: *{matched_voter.username}*.\n"
            f"Verified Phone: `{matched_voter.phone}`\n\n"
            f"You will now receive all your *Election OTPs* and verification codes instantly right here.\n\n"
            f"🏛️ _NECO MCS Electoral Committee (ELECO)_",
            reply_markup={"remove_keyboard": True},
        )
        logger.info(f"[Telegram] Successfully linked voter '{matched_voter.username}' ({matched_voter.full_name}) to chat_id '{chat_id}'")
        return

    # ── 2. /start COMMAND → Show phone share button and instructions ──
    if text.startswith("/start"):
        already_linked = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .first()
        )
        if already_linked:
            reply_tg(
                f"ℹ️ *Already Connected* ✅\n\n"
                f"Your Telegram is linked to voter *{already_linked.full_name}* (MCS: `{already_linked.username}`).\n"
                f"Registered Phone: `{already_linked.phone}`\n\n"
                f"You will receive all OTPs and election notifications here automatically.",
                reply_markup={"remove_keyboard": True},
            )
            return

        keyboard = {
            "keyboard": [
                [
                    {
                        "text": "📱 Share My Phone Number",
                        "request_contact": True,
                    }
                ]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        reply_tg(
            "🗳️ *Welcome to the NECO MCS Election OTP Bot!*\n\n"
            "To receive your Election OTPs here, please verify your registered phone number:\n\n"
            "👉 Tap the *'📱 Share My Phone Number'* button below.\n\n"
            "🔒 _For election integrity and security, manual typing of phone numbers is disabled. "
            "Telegram will securely confirm the SIM card registered on your active device._",
            reply_markup=keyboard,
        )
        return

    # ── 3. /status COMMAND → Check link status ──
    if text.startswith("/status"):
        user = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .first()
        )
        if user:
            reply_tg(
                f"ℹ️ *Status: Connected* ✅\n\n"
                f"Voter: *{user.full_name}*\n"
                f"MCS Number: `{user.username}`\n"
                f"Registered Phone: `{user.phone}`\n"
                f"Station: {user.staff_station or 'N/A'}\n"
                f"Accredited: {'Yes ✅' if user.is_accredited else 'Pending ⏳'}",
            )
        else:
            keyboard = {
                "keyboard": [[{"text": "📱 Share My Phone Number", "request_contact": True}]],
                "resize_keyboard": True,
                "one_time_keyboard": True,
            }
            reply_tg(
                "❌ *Not Connected*\n\n"
                "Your Telegram account is not yet linked to any voter.\n\n"
                "Tap the button below to link your registered phone number:",
                reply_markup=keyboard,
            )
        return

    # ── 3b. /unlink COMMAND → Self-service unlinking from Telegram ──
    if text.startswith("/unlink"):
        user = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .first()
        )
        if user:
            user.telegram_chat_id = None
            user.telegram_username = None
            db.commit()
            reply_tg(
                f"ℹ️ *Unlinked Successfully*\n\n"
                f"Your Telegram account has been disconnected from voter *{user.full_name}* (MCS: `{user.username}`).\n\n"
                f"You will no longer receive OTPs here. Tap /start anytime to re-link.",
                reply_markup={"remove_keyboard": True},
            )
        else:
            reply_tg(
                "Your Telegram account is not linked to any voter.",
                reply_markup={"remove_keyboard": True},
            )
        return

    # ── 4. Any other text (including manually typed numbers) → Security notice ──
    keyboard = {
        "keyboard": [
            [
                {
                    "text": "📱 Share My Phone Number",
                    "request_contact": True,
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }
    reply_tg(
        "🔒 *Security Notice: Manual Typing Disabled*\n\n"
        "To prevent voter impersonation and protect your vote, "
        "the bot *does not accept manually typed phone numbers*.\n\n"
        "👉 Please tap the *'📱 Share My Phone Number'* button below. "
        "Telegram will securely confirm the SIM card registered on your active device.",
        reply_markup=keyboard,
    )


# ============================================================
# TELEGRAM WEBHOOK ENDPOINT
# ============================================================
@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(database.get_db)):
    """Webhook called by Telegram when a user interacts with the bot."""
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message")
    if message:
        handle_telegram_incoming_message(message, db)

    return {"ok": True}


# ============================================================
# BACKGROUND LONG-POLLING WORKER
# ============================================================
def telegram_polling_worker():
    """
    Continuous background long-polling worker.
    Runs when webhooks cannot receive requests (e.g. self-signed SSL or raw IP).
    """
    bot_token = getattr(settings, "telegram_bot_token", None)
    if not bot_token:
        logger.info("[Telegram Polling] No bot token configured, skipping polling.")
        return

    logger.info("[Telegram Polling] Starting Telegram background polling worker...")
    offset = None

    # Clear any active webhook so getUpdates works reliably
    try:
        info_resp = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getWebhookInfo", timeout=10
        ).json()
        if info_resp.get("ok"):
            hook_url = info_resp.get("result", {}).get("url")
            if hook_url:
                logger.warning(f"[Telegram Polling] Clearing active webhook '{hook_url}' to enable polling.")
                requests.get(
                    f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=False",
                    timeout=10,
                )
    except Exception as e:
        logger.warning(f"[Telegram Polling] Could not check webhook info: {e}")

    while True:
        try:
            params = {"timeout": 20}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getUpdates",
                params=params,
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        msg = update.get("message") or update.get("edited_message")
                        if msg:
                            db = database.SessionLocal()
                            try:
                                handle_telegram_incoming_message(msg, db)
                            except Exception as ex:
                                logger.error(f"[Telegram Polling] Error handling message: {ex}")
                            finally:
                                db.close()
            elif resp.status_code == 409:
                time.sleep(10)
            else:
                time.sleep(3)
        except Exception:
            time.sleep(5)


def start_telegram_polling_thread():
    """Launches the Telegram polling worker in a background daemon thread."""
    if not getattr(settings, "telegram_bot_token", None):
        return
    thread = threading.Thread(target=telegram_polling_worker, daemon=True, name="TelegramPollingWorker")
    thread.start()
    logger.info("[Telegram Polling] Thread launched.")


# ============================================================
# GET TELEGRAM LINK INFO FOR A VOTER
# ============================================================
@router.get("/link-info/{username}")
def get_telegram_link_info(username: str, db: Session = Depends(database.get_db)):
    """Returns the Telegram bot link and current link status for a voter."""
    cleaned = username.strip()
    user = (
        db.query(user_models.User)
        .filter(func.lower(user_models.User.username) == cleaned.lower())
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter '{cleaned}' not found.",
        )

    bot_username = getattr(settings, "telegram_bot_username", "NECOMCSVotingOTPBot") or "NECOMCSVotingOTPBot"
    # No deep link parameter — voters link via phone number only
    deep_link = f"https://t.me/{bot_username}"

    return {
        "username": user.username,
        "full_name": user.full_name,
        "is_linked": bool(user.telegram_chat_id),
        "telegram_username": user.telegram_username,
        "deep_link": deep_link,
        "bot_username": f"@{bot_username}",
    }


# ============================================================
# TEST DISPATCH OTP VIA TELEGRAM
# ============================================================
@router.post("/test-send")
def test_send_telegram(
    payload: TelegramTestSendRequest,
    db: Session = Depends(database.get_db),
):
    """Test sending a sample OTP message to a voter's linked Telegram chat."""
    user = (
        db.query(user_models.User)
        .filter(func.lower(user_models.User.username) == payload.username.strip().lower())
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Voter not found.")

    if not user.telegram_chat_id:
        bot_username = getattr(settings, "telegram_bot_username", "NECOMCSVotingOTPBot") or "NECOMCSVotingOTPBot"
        raise HTTPException(
            status_code=400,
            detail=f"Voter '{user.username}' has not linked Telegram yet. "
                   f"Open https://t.me/{bot_username} and share your phone number to link.",
        )

    sent = send_otp_telegram(
        chat_id=user.telegram_chat_id,
        otp_code="123456",
        full_name=user.full_name,
        purpose_label="Test Verification",
    )

    return {
        "success": sent,
        "message": f"Test message dispatched to Telegram chat {user.telegram_chat_id}.",
        "voter": user.full_name,
        "telegram_username": user.telegram_username,
    }


# ============================================================
# UNLINK TELEGRAM ACCOUNT (Admin / Super-Admin only)
# ============================================================
@router.post("/unlink/{username}")
def unlink_voter_telegram(
    username: str,
    db: Session = Depends(database.get_db),
    current_admin: user_models.User = Depends(oauth2.get_current_user),
):
    """
    Allows Super Admin and Admin to unlink a voter's Telegram account.
    """
    if current_admin.role not in ("admin", "super-admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can unlink voter Telegram accounts.",
        )

    user = (
        db.query(user_models.User)
        .filter(func.lower(user_models.User.username) == username.strip().lower())
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail=f"Voter '{username}' not found.")

    old_chat_id = user.telegram_chat_id
    old_tg_user = user.telegram_username

    if not old_chat_id:
        return {
            "success": True,
            "message": f"Voter '{user.full_name}' (MCS: {user.username}) does not have a linked Telegram account.",
            "username": user.username,
        }

    # Notify voter on Telegram
    bot_token = getattr(settings, "telegram_bot_token", None)
    if bot_token and old_chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": old_chat_id,
                    "text": (
                        f"ℹ️ *Telegram Account Unlinked*\n\n"
                        f"Hello *{user.full_name}*,\n"
                        f"Your Telegram account has been unlinked from NECO MCS Voter ID: *{user.username}* by an election administrator.\n\n"
                        f"You will no longer receive OTPs here until re-linked.\n\n"
                        f"🏛️ _NECO MCS Electoral Committee (ELECO)_"
                    ),
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
        except Exception as e:
            logger.warning(f"Could not send unlink notice to voter: {e}")

    user.telegram_chat_id = None
    user.telegram_username = None
    db.commit()

    try:
        record_audit_log(
            db=db,
            admin_username=current_admin.username,
            action="UNLINK_TELEGRAM",
            target_type="USER",
            target_id=str(user.username),
            details=f"Admin '{current_admin.username}' unlinked Telegram ({old_tg_user or old_chat_id}) for voter '{user.username}' ({user.full_name}).",
            admin_id=current_admin.id,
        )
    except Exception as e:
        logger.warning(f"Could not record unlink audit log: {e}")

    return {
        "success": True,
        "message": f"Successfully unlinked Telegram for voter '{user.full_name}' (MCS: {user.username}).",
        "username": user.username,
    }

