import logging
import threading
import time
import requests
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from ..core import database
from ..core.config import settings
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
    - /start  → shows the "Share Phone Number" button
    - Contact → matches phone against registered voters, one-time link only
    - /status → check link status
    All other commands are ignored.
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

    # ── 1. CONTACT SHARING (Phone-number verification & one-time link) ──
    contact = message.get("contact")
    if contact:
        # Security: Telegram only allows sharing your OWN contact via request_contact.
        # The from.id must match the contact.user_id to prove ownership.
        contact_user_id = contact.get("user_id")
        sender_id = from_user.get("id")
        if contact_user_id and sender_id and str(contact_user_id) != str(sender_id):
            reply_tg(
                "🚫 *Security Violation*\n\n"
                "You can only share your *own* phone number, not someone else's contact.\n\n"
                "Please tap the *'📱 Share My Phone Number'* button to share your own verified number.",
                reply_markup={"remove_keyboard": True},
            )
            logger.warning(
                f"[Telegram] User {sender_id} tried to share contact of user {contact_user_id} — blocked."
            )
            return

        raw_phone = contact.get("phone_number", "")
        shared_suffix = _extract_last_10_digits(raw_phone)

        if not shared_suffix:
            reply_tg(
                "❌ *Invalid Phone Number*\n\n"
                "The phone number shared could not be processed. Please try again.",
                reply_markup={"remove_keyboard": True},
            )
            return

        # Check if this Telegram account is already linked to a voter
        already_linked = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .first()
        )
        if already_linked:
            reply_tg(
                f"⚠️ *Already Linked*\n\n"
                f"Your Telegram account is already linked to voter *{already_linked.full_name}* "
                f"(MCS: `{already_linked.username}`).\n\n"
                f"Each Telegram account can only be linked once. "
                f"If you need to change your linked account, please contact the Electoral Committee (ELECO).",
                reply_markup={"remove_keyboard": True},
            )
            return

        # Find voter by matching the last 10 digits of the phone number
        all_voters = (
            db.query(user_models.User)
            .filter(user_models.User.phone.isnot(None))
            .all()
        )
        matched_voter = None
        for voter in all_voters:
            voter_suffix = _extract_last_10_digits(voter.phone)
            if voter_suffix and voter_suffix == shared_suffix:
                matched_voter = voter
                break

        if not matched_voter:
            reply_tg(
                "❌ *Phone Number Not Registered*\n\n"
                "The phone number you shared does not match any registered voter "
                "in the NECO MCS Electoral System.\n\n"
                "⚠️ Only voters whose phone numbers are registered on the official "
                "NECO MCS voters roll can link their Telegram accounts.\n\n"
                "If you believe this is an error, please contact the Electoral Committee (ELECO).",
                reply_markup={"remove_keyboard": True},
            )
            logger.info(f"[Telegram] Phone '{raw_phone}' not found in voters roll. chat_id={chat_id}")
            return

        # Check if this voter's account is already linked to a DIFFERENT Telegram
        if matched_voter.telegram_chat_id and matched_voter.telegram_chat_id != chat_id:
            reply_tg(
                "🚫 *Account Already Linked*\n\n"
                "This voter account is already linked to a different Telegram account.\n\n"
                "Each voter can only link their Telegram *once*. "
                "If you believe this is an error, please contact the Electoral Committee (ELECO).",
                reply_markup={"remove_keyboard": True},
            )
            logger.warning(
                f"[Telegram] Voter '{matched_voter.username}' already linked to chat_id "
                f"'{matched_voter.telegram_chat_id}', rejected re-link attempt from chat_id '{chat_id}'."
            )
            return

        # ✅ Phone matched & not yet linked → link now
        matched_voter.telegram_chat_id = chat_id
        matched_voter.telegram_username = (
            f"@{tg_username}" if not tg_username.startswith("@") else tg_username
        )
        db.commit()

        reply_tg(
            f"✅ *Phone Number Verified & Linked!*\n\n"
            f"Hello *{matched_voter.full_name}*,\n"
            f"Your Telegram account has been securely linked to your NECO MCS Voter ID: "
            f"*{matched_voter.username}*.\n\n"
            f"You will now receive all your *Election OTPs* and verification codes "
            f"instantly right here.\n\n"
            f"🔒 _This link is permanent and cannot be changed without ELECO approval._\n\n"
            f"🏛️ _NECO MCS Electoral Committee (ELECO)_",
            reply_markup={"remove_keyboard": True},
        )
        logger.info(
            f"[Telegram] Linked voter '{matched_voter.username}' ({matched_voter.full_name}) "
            f"via phone match to chat_id '{chat_id}'."
        )
        return

    # ── 2. /start COMMAND → Show phone share button ──
    if text.startswith("/start"):
        # Check if already linked
        already_linked = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .first()
        )
        if already_linked:
            reply_tg(
                f"ℹ️ *Already Connected*\n\n"
                f"Your Telegram is linked to voter *{already_linked.full_name}* "
                f"(MCS: `{already_linked.username}`).\n\n"
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
            "To receive your Election OTPs here, we need to verify your identity "
            "using your *registered phone number*.\n\n"
            "👇 Tap the button below to securely share your phone number:\n\n"
            "🔒 _Your phone number will be matched against the official NECO MCS "
            "voters roll. Only registered voters can link their accounts._",
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
                f"Station: {user.staff_station or 'N/A'}\n"
                f"Accredited: {'Yes ✅' if user.is_accredited else 'Pending ⏳'}",
            )
        else:
            reply_tg(
                "❌ *Not Connected*\n\n"
                "Your Telegram account is not linked to any voter.\n\n"
                "Send /start to begin the phone verification process.",
            )
        return

    # ── 4. Any other text → Inform user ──
    reply_tg(
        "ℹ️ This bot only supports phone-number-based linking.\n\n"
        "Available commands:\n"
        "• /start — Begin phone verification\n"
        "• /status — Check your link status",
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

    # Clear any failing webhook so getUpdates works
    try:
        info_resp = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getWebhookInfo", timeout=10
        ).json()
        if info_resp.get("ok"):
            hook_url = info_resp.get("result", {}).get("url")
            last_err = info_resp.get("result", {}).get("last_error_message")
            if hook_url and last_err:
                logger.warning(f"[Telegram Polling] Clearing failing webhook '{hook_url}' ({last_err})")
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
