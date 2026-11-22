import logging
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
# 1. TELEGRAM WEBHOOK (Receives events from Telegram Bot API)
# ============================================================
@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(database.get_db)):
    """
    Webhook called by Telegram when a user interacts with the bot.
    Handles:
      /start MCS_<username>  -> Automatically links voter's chat_id to their account.
      /status                -> Checks linkage status.
      /help                  -> Instructions.
    """
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    text = (message.get("text") or "").strip()
    from_user = message.get("from", {})
    tg_username = from_user.get("username") or from_user.get("first_name", "Member")

    bot_token = getattr(settings, "telegram_bot_token", None)

    def reply_tg(reply_text: str):
        if not bot_token:
            logger.info(f"[SIMULATED TG REPLY to {chat_id}]: {reply_text}")
            return
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            logger.error(f"Error sending Telegram reply: {e}")

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
                    f"🏛️ _NECO MCS Electoral Committee (ELECO)_"
                )
                logger.info(f"Linked voter '{user.username}' ({user.full_name}) to Telegram chat_id '{chat_id}'")
                return {"ok": True}
            else:
                reply_tg(
                    f"⚠️ *Voter Not Found*\n\n"
                    f"Could not find a voter record for MCS number `{target_username}`. "
                    f"Please verify your 4-digit MCS number on the election portal."
                )
                return {"ok": True}
        else:
            # Bare /start command
            reply_tg(
                f"🗳️ *Welcome to the NECO MCS Election Bot!*\n\n"
                f"To link your account and receive instant OTPs here:\n"
                f"1. Log in to the NECO MCS Portal: {settings.api_base_url.replace('/api', '')}\n"
                f"2. Click the *'Connect Telegram'* button on your screen.\n\n"
                f"Alternatively, you can send: `/link YOUR_MCS_NUMBER`\n"
                f"Example: `/link 1072`"
            )
            return {"ok": True}

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
                    f"You will now receive your voting verification OTPs here."
                )
                return {"ok": True}
            else:
                reply_tg(f"❌ No registered voter found with MCS number: `{target_username}`.")
                return {"ok": True}
        else:
            reply_tg("Please provide your MCS number. Example: `/link 1072`")
            return {"ok": True}

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
        return {"ok": True}

    return {"ok": True}


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

    bot_username = getattr(settings, "telegram_bot_username", "NECOMCSVotingBot") or "NECOMCSVotingBot"
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
        bot_username = getattr(settings, "telegram_bot_username", "NECOMCSVotingBot") or "NECOMCSVotingBot"
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
