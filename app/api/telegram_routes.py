import logging
import threading
import time
import requests
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, text
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
# Persistent + In-memory store for pending link sessions
# Uses both DB column User.telegram_link_session and in-memory fallback
# ============================================================
_pending_link_sessions: dict[str, str] = {}
_session_column_checked: bool = False


def _ensure_session_column(db: Session):
    global _session_column_checked
    if _session_column_checked:
        return
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_link_session VARCHAR(100);"))
        db.commit()
        _session_column_checked = True
    except Exception:
        db.rollback()


def _get_intended_voter(chat_id: str, db: Session):
    """Find the voter that this chat_id is currently attempting to link."""
    _ensure_session_column(db)
    # 1. Check database column on users table
    try:
        voter = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_link_session == chat_id)
            .first()
        )
        if voter:
            return voter
    except Exception as e:
        logger.warning(f"Error querying telegram_link_session: {e}")
        db.rollback()

    # 2. Check in-memory session fallback
    uname = _pending_link_sessions.get(chat_id)
    if uname:
        return (
            db.query(user_models.User)
            .filter(func.lower(user_models.User.username) == uname.lower())
            .first()
        )
    return None


def _set_intended_voter_session(chat_id: str, voter: user_models.User, db: Session):
    """Set the linking session in both DB and memory."""
    _ensure_session_column(db)
    try:
        db.query(user_models.User).filter(user_models.User.telegram_link_session == chat_id).update(
            {"telegram_link_session": None}
        )
        voter.telegram_link_session = chat_id
        db.commit()
    except Exception as e:
        logger.warning(f"Error setting telegram_link_session: {e}")
        db.rollback()
    _pending_link_sessions[chat_id] = voter.username


def _clear_intended_voter_session(chat_id: str, db: Session):
    """Clear the linking session from DB and memory."""
    _ensure_session_column(db)
    try:
        db.query(user_models.User).filter(user_models.User.telegram_link_session == chat_id).update(
            {"telegram_link_session": None}
        )
        db.commit()
    except Exception:
        db.rollback()
    _pending_link_sessions.pop(chat_id, None)


# ============================================================
# CORE MESSAGE HANDLER (Webhook + Polling)
# ============================================================
def handle_telegram_incoming_message(message: dict, db: Session):
    """
    Secure phone-number linking with username verification.
    Flow:
      1. Voter clicks "Connect" on the web app → opens deep link /start <username>.
      2. Bot stores the intended username and shows the "Share My Phone Number" button.
      3. When voter taps the button, bot verifies that the shared phone matches
         the stored username's registered phone. If mismatch → rejected.
      4. /status - Checks current link status.
      5. /unlink - Self-service unlinking.
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

        # Check who this chat is currently linked to
        already_linked = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .first()
        )

        # ── Find the intended voter for this linking attempt ──
        intended_voter = _get_intended_voter(chat_id, db)

        if not intended_voter:
            if already_linked:
                reply_tg(
                    f"ℹ️ *Already Connected* ✅\n\n"
                    f"Your Telegram is already linked to voter *{already_linked.full_name}* (MCS: `{already_linked.username}`).\n"
                    f"Registered Phone: `{already_linked.phone}`\n\n"
                    f"If you need to link a different voter account, first send /unlink.",
                    reply_markup={"remove_keyboard": True},
                )
                return

            keyboard = {
                "keyboard": [[{"text": "📱 Share My Phone Number", "request_contact": True}]],
                "resize_keyboard": True,
                "one_time_keyboard": True,
            }
            reply_tg(
                "ℹ️ *Voter Identification Required*\n\n"
                "Before sharing your phone number, please enter your **MCS Voter Number** (e.g. `2668`) in this chat, or click **Connect** from the voter accreditation portal.\n\n"
                "🔒 _The system needs to verify that your shared phone matches that specific voter profile._",
                reply_markup=keyboard,
            )
            return

        # ── Verify the shared phone belongs to the intended voter ──
        intended_phone_suffix = _extract_last_10_digits(intended_voter.phone) if intended_voter.phone else None

        if not intended_phone_suffix or intended_phone_suffix != shared_suffix:
            # MISMATCH! Block linking immediately and clear session.
            _clear_intended_voter_session(chat_id, db)
            clean_display = raw_phone.strip()
            reply_tg(
                f"🚫 *Phone Number Mismatch (Linking Blocked)*\n\n"
                f"You attempted to link voter *{intended_voter.full_name}* (MCS: `{intended_voter.username}`).\n\n"
                f"However, the phone number shared from your Telegram (`{clean_display}`) does **not** match the official phone registered on voter `{intended_voter.username}`'s record.\n\n"
                f"⚠️ *Security Protection:* You can only link your *own* voter account. Using another person's MCS number or linking a phone number that does not match the official voters roll is strictly prohibited.\n\n"
                f"If you believe your registered phone number is outdated, please use the Voter Contact Update portal or contact ELECO.",
                reply_markup={"remove_keyboard": True},
            )
            logger.warning(
                f"[Telegram Security] BLOCKED cross-account linking: Chat {chat_id} shared phone {raw_phone} (suffix {shared_suffix}) "
                f"for voter '{intended_voter.username}' (expected suffix {intended_phone_suffix})"
            )
            return

        # Phone matches the intended voter!
        # Check if this voter is ALREADY linked to this chat
        if intended_voter.telegram_chat_id == chat_id:
            _clear_intended_voter_session(chat_id, db)
            reply_tg(
                f"✅ *Already Connected!*\n\n"
                f"Hello *{intended_voter.full_name}*,\n"
                f"Your Telegram is already securely linked to your Voter ID: *{intended_voter.username}*.\n"
                f"Registered Phone: `{intended_voter.phone}`\n\n"
                f"You will receive all Election OTPs and notifications right here.",
                reply_markup={"remove_keyboard": True},
            )
            return

        # Check if voter is already linked to another chat
        if intended_voter.telegram_chat_id and intended_voter.telegram_chat_id != chat_id:
            _clear_intended_voter_session(chat_id, db)
            reply_tg(
                f"🚫 *Account Already Linked*\n\n"
                f"Voter profile *{intended_voter.full_name}* (MCS: `{intended_voter.username}`) is already linked to another Telegram account.\n\n"
                f"Each voter can only link their Telegram once. Please contact ELECO if you need assistance.",
                reply_markup={"remove_keyboard": True},
            )
            logger.warning(f"[Telegram] Voter '{intended_voter.username}' already linked to chat {intended_voter.telegram_chat_id}")
            return

        # Check if chat is already linked to another voter
        if already_linked and already_linked.id != intended_voter.id:
            _clear_intended_voter_session(chat_id, db)
            reply_tg(
                f"⚠️ *Telegram Account Already In Use*\n\n"
                f"This Telegram account is currently linked to voter *{already_linked.full_name}* (MCS: `{already_linked.username}`).\n\n"
                f"Please send /unlink first if you wish to switch voter accounts.",
                reply_markup={"remove_keyboard": True},
            )
            return

        # Success! Link intended voter
        intended_voter.telegram_chat_id = chat_id
        intended_voter.telegram_username = f"@{tg_username}" if not tg_username.startswith("@") else tg_username
        intended_voter.telegram_link_session = None
        db.commit()
        _pending_link_sessions.pop(chat_id, None)

        reply_tg(
            f"✅ *Phone Number Verified & Linked!*\n\n"
            f"Hello *{intended_voter.full_name}*,\n"
            f"Your Telegram account has been linked to your NECO MCS Voter ID: *{intended_voter.username}*.\n"
            f"Verified Phone: `{intended_voter.phone}`\n\n"
            f"You will now receive all your *Election OTPs* and verification codes instantly right here.\n\n"
            f"🏛️ _NECO MCS Electoral Committee (ELECO)_",
            reply_markup={"remove_keyboard": True},
        )
        logger.info(f"[Telegram] Successfully linked voter '{intended_voter.username}' ({intended_voter.full_name}) to chat_id '{chat_id}'")
        return

    # ── 2. /start COMMAND → Set intended voter session & show phone share button ──
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        start_param = parts[1].strip() if len(parts) > 1 else None

        already_linked = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .first()
        )

        if start_param:
            target_voter = (
                db.query(user_models.User)
                .filter(func.lower(user_models.User.username) == start_param.lower())
                .first()
            )
            if not target_voter:
                reply_tg(
                    f"❌ *Voter Not Found*\n\n"
                    f"MCS number `{start_param}` was not found on the official voters roll.\n\n"
                    f"Please check your MCS number on the accreditation portal and try again.",
                    reply_markup={"remove_keyboard": True},
                )
                return

            if already_linked and already_linked.id == target_voter.id:
                reply_tg(
                    f"✅ *Already Connected!*\n\n"
                    f"Hello *{already_linked.full_name}*,\n"
                    f"Your Telegram is already securely linked to your Voter ID: *{already_linked.username}*.\n"
                    f"Registered Phone: `{already_linked.phone}`\n\n"
                    f"You will receive all Election OTPs and notifications right here.",
                    reply_markup={"remove_keyboard": True},
                )
                return

            if already_linked and already_linked.id != target_voter.id:
                reply_tg(
                    f"🚫 *Account Conflict*\n\n"
                    f"Your Telegram account is currently linked to voter *{already_linked.full_name}* (MCS: `{already_linked.username}`).\n\n"
                    f"You cannot link it to voter *{target_voter.full_name}* (MCS: `{target_voter.username}`) unless you unlink first.\n\n"
                    f"To unlink your current account, send /unlink.",
                    reply_markup={"remove_keyboard": True},
                )
                return

            if target_voter.telegram_chat_id and target_voter.telegram_chat_id != chat_id:
                reply_tg(
                    f"🚫 *Account Already Linked*\n\n"
                    f"Voter profile *{target_voter.full_name}* (MCS: `{target_voter.username}`) is already linked to another Telegram account.\n\n"
                    f"Each voter can only link their Telegram once. Please contact ELECO if you need assistance.",
                    reply_markup={"remove_keyboard": True},
                )
                return

            _set_intended_voter_session(chat_id, target_voter, db)
            logger.info(f"[Telegram] Linking session started: chat {chat_id} → voter '{target_voter.username}'")

            keyboard = {
                "keyboard": [[{"text": "📱 Share My Phone Number", "request_contact": True}]],
                "resize_keyboard": True,
                "one_time_keyboard": True,
            }
            masked_phone = target_voter.phone[-4:] if target_voter.phone else "N/A"
            reply_tg(
                f"🗳️ *Linking Verification: MCS {target_voter.username}*\n\n"
                f"Hello! You are linking Telegram for voter *{target_voter.full_name}* (MCS: `{target_voter.username}`).\n\n"
                f"👉 Tap the *'📱 Share My Phone Number'* button below to verify your identity.\n\n"
                f"🔒 *Security Check:* Telegram will verify your active SIM card. It MUST match the registered phone for MCS `{target_voter.username}` (ending in `...{masked_phone}`). If the numbers do not match, the link will be blocked.",
                reply_markup=keyboard,
            )
            return

        # No start_param:
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
            "keyboard": [[{"text": "📱 Share My Phone Number", "request_contact": True}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        reply_tg(
            "🗳️ *Welcome to the NECO MCS Election OTP Bot!*\n\n"
            "To link your Telegram account:\n\n"
            "1. Enter your **MCS Voter Number** (e.g. `2668`) in this chat, OR\n"
            "2. Click **Connect** from the voter accreditation portal.\n\n"
            "🏛️ _NECO MCS Electoral Committee (ELECO)_",
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
                "Enter your MCS Voter Number (e.g. `2668`) or click Connect from the accreditation portal.",
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
        _clear_intended_voter_session(chat_id, db)
        if user:
            user.telegram_chat_id = None
            user.telegram_username = None
            db.commit()
            reply_tg(
                f"ℹ️ *Unlinked Successfully*\n\n"
                f"Your Telegram account has been disconnected from voter *{user.full_name}* (MCS: `{user.username}`).\n\n"
                f"You will no longer receive OTPs here. Enter your MCS number anytime to re-link.",
                reply_markup={"remove_keyboard": True},
            )
        else:
            reply_tg(
                "Your Telegram account is not linked to any voter.",
                reply_markup={"remove_keyboard": True},
            )
        return

    # ── 4. Any other text → Check if it's an MCS Number ──
    clean_text = text.strip()
    target_voter = (
        db.query(user_models.User)
        .filter(func.lower(user_models.User.username) == clean_text.lower())
        .first()
    )
    if target_voter:
        already_linked = (
            db.query(user_models.User)
            .filter(user_models.User.telegram_chat_id == chat_id)
            .first()
        )
        if already_linked and already_linked.id == target_voter.id:
            reply_tg(
                f"✅ *Already Connected!*\n\n"
                f"Hello *{already_linked.full_name}*,\n"
                f"Your Telegram is already securely linked to your Voter ID: *{already_linked.username}*.\n"
                f"Registered Phone: `{already_linked.phone}`\n\n"
                f"You will receive all Election OTPs and notifications right here.",
                reply_markup={"remove_keyboard": True},
            )
            return

        if already_linked and already_linked.id != target_voter.id:
            reply_tg(
                f"🚫 *Account Conflict*\n\n"
                f"Your Telegram account is currently linked to voter *{already_linked.full_name}* (MCS: `{already_linked.username}`).\n\n"
                f"You cannot link it to voter *{target_voter.full_name}* (MCS: `{target_voter.username}`) unless you unlink first.\n\n"
                f"To unlink your current account, send /unlink.",
                reply_markup={"remove_keyboard": True},
            )
            return

        if target_voter.telegram_chat_id and target_voter.telegram_chat_id != chat_id:
            reply_tg(
                f"🚫 *Account Already Linked*\n\n"
                f"Voter profile *{target_voter.full_name}* (MCS: `{target_voter.username}`) is already linked to another Telegram account.\n\n"
                f"Each voter can only link their Telegram once. Please contact ELECO if you need assistance.",
                reply_markup={"remove_keyboard": True},
            )
            return

        _set_intended_voter_session(chat_id, target_voter, db)
        keyboard = {
            "keyboard": [[{"text": "📱 Share My Phone Number", "request_contact": True}]],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        masked_phone = target_voter.phone[-4:] if target_voter.phone else "N/A"
        reply_tg(
            f"🗳️ *Voter Identified: {target_voter.full_name} (MCS: {target_voter.username})*\n\n"
            f"To complete verification, please tap the *'📱 Share My Phone Number'* button below.\n\n"
            f"🔒 *Security Check:* Telegram will verify your active SIM card. It MUST match the registered phone for MCS `{target_voter.username}` (ending in `...{masked_phone}`). If the numbers do not match, the link will be rejected.",
            reply_markup=keyboard,
        )
        return

    # If text is not an MCS number:
    keyboard = {
        "keyboard": [[{"text": "📱 Share My Phone Number", "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }
    reply_tg(
        "🔒 *Security Notice*\n\n"
        "To link your Telegram account:\n"
        "1. Enter your **MCS Voter Number** (e.g. `2668`) in this chat, OR\n"
        "2. Click **Connect** from the voter accreditation portal.\n\n"
        "Then tap the *'📱 Share My Phone Number'* button to verify your SIM card.",
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
    # Deep link with username so the bot knows which voter is linking
    deep_link = f"https://t.me/{bot_username}?start={user.username}"

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

