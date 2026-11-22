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
from ..domain import user as user_models
from ..core.otp_utils import send_otp_telegram

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{settings.api_prefix}/telegram", tags=["Telegram Bot"])


class TelegramManualLinkRequest(BaseModel):
    username: str
    chat_id: str
    telegram_username: Optional[str] = None


class TelegramTestSendRequest(BaseModel):
    username: str
    message: Optional[str] = "This is a test notification from the NECO MCS Electronic Voting System."


# ============================================================
# HELPER: Process incoming message from Webhook or Polling
# ============================================================
def handle_telegram_incoming_message(message: dict, db: Session):
    """
    Core message processor used by both Webhook and Background Polling.
    Handles /start MCS_<username>, /link <username>, and /status.
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
            requests.post(
                url,
                json=payload,
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Error sending Telegram reply: {e}")

    # Handle Contact Sharing (User taps "Share Contact" button)
    contact = message.get("contact")
    if contact:
        raw_phone = contact.get("phone_number", "")
        clean_digits = "".join(ch for ch in str(raw_phone) if ch.isdigit())
        if len(clean_digits) >= 10:
            suffix = clean_digits[-10:]
            user = (
                db.query(user_models.User)
                .filter(user_models.User.phone.like(f"%{suffix}"))
                .first()
            )
            if user:
                user.telegram_chat_id = chat_id
                user.telegram_username = f"@{tg_username}" if not tg_username.startswith("@") else tg_username
                db.commit()

                reply_tg(
                    f"✅ *Phone Number Verified & Linked!*\n\n"
                    f"Hello *{user.full_name}*,\n"
                    f"Your Telegram account has been linked to your NECO MCS Voter ID: *{user.username}* (Phone: `{user.phone}`).\n\n"
                    f"You will now receive all your *Election OTPs* and verification codes instantly right here.\n\n"
                    f"🏛️ _NECO MCS Electoral Committee (ELECO)_",
                    reply_markup={"remove_keyboard": True},
                )
                logger.info(f"Linked voter '{user.username}' via phone number '{raw_phone}' to Telegram chat_id '{chat_id}'")
                return
            else:
                reply_tg(
                    f"❌ *Phone Number Not Registered*\n\n"
                    f"The phone number you shared does not match any registered voter in the NECO MCS Electoral System.\n\n"
                    f"⚠️ Only voters whose phone numbers are registered on the official NECO MCS voters roll can link their Telegram accounts.\n\n"
                    f"If you believe this is an error, please contact the Electoral Committee (ELECO).",
                    reply_markup={"remove_keyboard": True},
                )
                return

    # Handle /start with deep link parameter (e.g. /start MCS_1072)
    if text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1:
            payload = parts[1].strip()
            # Normalize payload (support MCS_1072, LINK_1072, or bare 1072)
            target_username = payload
            for prefix in ("MCS_", "LINK_", "mcs_", "link_"):
                if target_username.startswith(prefix):
                    target_username = target_username[len(prefix):]
                    break

            # Look up user by username
            user = (
                db.query(user_models.User)
                .filter(func.lower(user_models.User.username) == target_username.lower())
                .first()
            )

            if user:
                user.telegram_chat_id = chat_id
                user.telegram_username = f"@{tg_username}" if not tg_username.startswith("@") else tg_username
                db.commit()

                reply_tg(
                    f"✅ *Telegram Successfully Linked!*\n\n"
                    f"Hello *{user.full_name}*,\n"
                    f"Your Telegram account has been linked to your NECO MCS Voter ID: *{user.username}*.\n\n"
                    f"You will now receive all your *Election OTPs*, accreditation codes, and voting notifications instantly right here.\n\n"
                    f"🏛️ _NECO MCS Electoral Committee (ELECO)_",
                    reply_markup={"remove_keyboard": True},
                )
                logger.info(f"Linked voter '{user.username}' ({user.full_name}) to Telegram chat_id '{chat_id}'")
            else:
                reply_tg(
                    f"⚠️ *Voter Not Found*\n\n"
                    f"Could not find a voter record for MCS number `{target_username}`. "
                    f"Please verify your 4-digit MCS number on the election portal.",
                    reply_markup={"remove_keyboard": True},
                )
        else:
            # Bare /start command: show friendly instructions and phone share button!
            keyboard = {
                "keyboard": [
                    [
                        {
                            "text": "📱 Tap to Link with My Phone Number",
                            "request_contact": True,
                        }
                    ]
                ],
                "resize_keyboard": True,
                "one_time_keyboard": True,
            }
            reply_tg(
                f"🗳️ *Welcome to the NECO MCS Election OTP Bot!*\n\n"
                f"To receive your Election OTPs here instantly:\n\n"
                f"1. Tap the *'📱 Tap to Link with My Phone Number'* button below\n"
                f"OR\n"
                f"2. Send your MCS number: `/link YOUR_MCS_NUMBER`\n"
                f"   (Example: `/link 2668`)",
                reply_markup=keyboard,
            )

    # Handle /link <username>
    elif text.startswith("/link"):
        parts = text.split()
        if len(parts) > 1:
            target_username = parts[1].strip()
            user = (
                db.query(user_models.User)
                .filter(func.lower(user_models.User.username) == target_username.lower())
                .first()
            )
            if user:
                user.telegram_chat_id = chat_id
                user.telegram_username = f"@{tg_username}" if not tg_username.startswith("@") else tg_username
                db.commit()

                reply_tg(
                    f"✅ *Linked Successfully!*\n\n"
                    f"Connected to voter: *{user.full_name}* (MCS: `{user.username}`).\n"
                    f"You will now receive your voting verification OTPs here.",
                    reply_markup={"remove_keyboard": True},
                )
            else:
                reply_tg(
                    f"❌ No registered voter found with MCS number: `{target_username}`.",
                    reply_markup={"remove_keyboard": True},
                )
        else:
            reply_tg("Please provide your MCS number. Example: `/link 1072`")

    # Handle /status
    elif text.startswith("/status"):
        user = db.query(user_models.User).filter(user_models.User.telegram_chat_id == chat_id).first()
        if user:
            reply_tg(
                f"ℹ️ *Status: Connected*\n\n"
                f"Voter: *{user.full_name}*\n"
                f"MCS Number: `{user.username}`\n"
                f"Station: {user.staff_station or 'N/A'}\n"
                f"Accredited: {'Yes ✅' if user.is_accredited else 'Pending ⏳'}"
            )
        else:
            reply_tg("❌ Your Telegram account is not yet linked to any voter. Send `/link YOUR_MCS_NUMBER` to connect.")


# ============================================================
# 1. TELEGRAM WEBHOOK (Receives events from Telegram Bot API)
# ============================================================
@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(database.get_db)):
    """
    Webhook called by Telegram when a user interacts with the bot.
    """
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message")
    if message:
        handle_telegram_incoming_message(message, db)

    return {"ok": True}


# ============================================================
# BACKGROUND LONG-POLLING WORKER (Self-healing fallback)
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

    # Check if a failing webhook is registered; clear it so getUpdates succeeds
    try:
        info_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo", timeout=10).json()
        if info_resp.get("ok"):
            hook_url = info_resp.get("result", {}).get("url")
            last_err = info_resp.get("result", {}).get("last_error_message")
            if hook_url and last_err:
                logger.warning(f"[Telegram Polling] Clearing failing webhook '{hook_url}' ({last_err})")
                requests.get(f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=False", timeout=10)
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
                # 409 Conflict: A webhook is active or another instance is polling
                time.sleep(10)
            else:
                time.sleep(3)
        except Exception as e:
            time.sleep(5)


def start_telegram_polling_thread():
    """
    Launches the Telegram polling worker in a background daemon thread.
    """
    if not getattr(settings, "telegram_bot_token", None):
        return
    thread = threading.Thread(target=telegram_polling_worker, daemon=True, name="TelegramPollingWorker")
    thread.start()
    logger.info("[Telegram Polling] Thread launched.")


# ============================================================
# 2. GET TELEGRAM LINK INFO & DEEP LINK FOR A VOTER
# ============================================================
@router.get("/link-info/{username}")
def get_telegram_link_info(username: str, db: Session = Depends(database.get_db)):
    """
    Returns the one-click Telegram deep link and current link status for a voter.
    """
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
    deep_link = f"https://t.me/{bot_username}?start=MCS_{user.username}"

    return {
        "username": user.username,
        "full_name": user.full_name,
        "is_linked": bool(user.telegram_chat_id),
        "telegram_username": user.telegram_username,
        "deep_link": deep_link,
        "bot_username": f"@{bot_username}",
    }


# ============================================================
# 3. MANUAL LINK (For Admin or Direct API setup)
# ============================================================
@router.post("/manual-link")
def manual_link_telegram(
    payload: TelegramManualLinkRequest,
    db: Session = Depends(database.get_db),
):
    """
    Manually link a voter's account with a Telegram chat ID.
    """
    user = (
        db.query(user_models.User)
        .filter(func.lower(user_models.User.username) == payload.username.strip().lower())
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Voter not found.")

    user.telegram_chat_id = payload.chat_id.strip()
    if payload.telegram_username:
        user.telegram_username = payload.telegram_username.strip()
    db.commit()

    return {
        "message": f"Successfully linked voter '{user.username}' to Telegram chat_id '{user.telegram_chat_id}'.",
        "username": user.username,
        "full_name": user.full_name,
        "telegram_chat_id": user.telegram_chat_id,
        "telegram_username": user.telegram_username,
    }


# ============================================================
# 4. TEST DISPATCH OTP VIA TELEGRAM
# ============================================================
@router.post("/test-send")
def test_send_telegram(
    payload: TelegramTestSendRequest,
    db: Session = Depends(database.get_db),
):
    """
    Test sending a sample OTP message to a voter's linked Telegram chat.
    """
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
            detail=f"Voter '{user.username}' has not linked Telegram yet. Click https://t.me/{bot_username}?start=MCS_{user.username} first.",
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
