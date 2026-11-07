import secrets
import smtplib
import logging
import os
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone

from .config import settings

logger = logging.getLogger(__name__)


# ============================================================
# OTP GENERATION & PRIVACY HELPERS
# ============================================================

def mask_email(email: str | None) -> str | None:
    """Mask email for privacy, e.g. thom********@gmail.com."""
    if not email or "@" not in email:
        return email
    parts = email.split("@", 1)
    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = name[0] + "*" * max(1, len(name) - 1)
    elif len(name) <= 4:
        masked_name = name[:2] + "*" * (len(name) - 2)
    else:
        masked_name = name[:4] + "*" * max(8, len(name) - 4)
    return f"{masked_name}@{domain}"


def mask_phone(phone: str | None) -> str | None:
    """Mask phone for privacy, e.g. ********957 (preserving last 3 digits)."""
    if not phone:
        return phone
    clean = str(phone).strip()
    if len(clean) <= 3:
        return "*" * len(clean)
    return "*" * (len(clean) - 3) + clean[-3:]


def normalize_nigerian_phone(phone: str | None) -> str | None:
    """
    Normalizes Nigerian phone numbers to international format (234XXXXXXXXXX).
    Examples:
      08031234567   -> 2348031234567
      +2348031234567 -> 2348031234567
      2348031234567  -> 2348031234567
    """
    if not phone:
        return None
    raw = str(phone).strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return None
    if raw.startswith("+234") or digits.startswith("234"):
        return digits
    if digits.startswith("0") and len(digits) == 11:
        return "234" + digits[1:]
    if len(digits) == 10:
        return "234" + digits
    return digits


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def get_otp_expiry(minutes: int = 10) -> datetime:
    """Return a timezone-aware expiry datetime."""
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


# ============================================================
# EMAIL DELIVERY
# ============================================================

def send_otp_email(
    recipient_email: str, 
    otp_code: str, 
    full_name: str,
    subject: str = "NECO MCS Verification",
    purpose_label: str = "Verification"
) -> bool:
    """Send OTP to the user's email address via SMTP."""
    if not recipient_email:
        logger.warning("No email address provided – skipping email OTP delivery.")
        return False

    html_body = f"""
    <html>
      <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b; max-width: 600px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
        <div style="text-align: center; margin-bottom: 24px;">
          <h2 style="color: #4f46e5; margin: 0; font-size: 24px;">🗳️ NECO MCS Election</h2>
          <p style="color: #64748b; margin-top: 4px; font-weight: 600;">{subject}</p>
        </div>
        <p>Hello <strong>{full_name}</strong>,</p>
        <p>Your One-Time Password (OTP) for <strong>{purpose_label}</strong> is:</p>
        <div style="background:#eef2ff; border: 2px dashed #6366f1; padding: 20px; margin: 24px 0; border-radius: 8px; text-align: center;">
          <span style="font-family: monospace; font-size: 32px; letter-spacing: 12px; font-weight: 700; color: #4338ca;">{otp_code}</span>
        </div>
        <p>This OTP is strictly confidential and is valid for <strong>{settings.otp_expire_minutes} minutes</strong>.</p>
        <p style="color: #dc2626; font-size: 13px; font-weight: 500;">Do not share this code with anyone. Election officials will never ask for your OTP.</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin-top: 32px;">
        <p style="color: #94a3b8; font-size: 12px; text-align: center;">NECO MCS Secure Electronic Voting System</p>
      </body>
    </html>
    """

    # If SMTP username or password not configured, log OTP for dev/testing
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning(f"SMTP not configured. [DEV SIMULATION] Header='{subject}' Recipient='{recipient_email}' OTP='{otp_code}'")
        print(f"\n========================================\n[EMAIL OTP] Header: {subject}\nTo: {recipient_email}\nCode: {otp_code}\n========================================\n")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender_email or settings.smtp_username
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(msg["From"], recipient_email, msg.as_string())
        logger.info(f"OTP email sent to {recipient_email} with subject '{subject}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {recipient_email}: {e}")
        # In dev or if SMTP fails, fallback to printing so app can still be tested
        if settings.environment == "development":
            print(f"\n[DEV FALLBACK OTP] Header: {subject} To: {recipient_email} Code: {otp_code}\n")
            return True
        return False


# ============================================================
# SMS DELIVERY (Termii with Twilio Fallback)
# ============================================================

def send_otp_sms(
    phone_number: str, 
    otp_code: str, 
    purpose_label: str = "Verification"
) -> bool:
    """
    Send OTP via Termii SMS (cheap Nigerian route with DND handling).
    Falls back to Twilio if Termii is not configured.
    """
    if not phone_number:
        logger.warning("No phone number provided – skipping SMS OTP delivery.")
        return False

    clean_phone = normalize_nigerian_phone(phone_number)
    if not clean_phone:
        logger.warning(f"Invalid phone number '{phone_number}' – skipping SMS OTP delivery.")
        return False

    # 1. Termii Gateway (Preferred Nigerian Provider)
    termii_api_key = getattr(settings, "termii_api_key", None) or os.getenv("TERMII_API_KEY")
    if termii_api_key:
        sender_id = getattr(settings, "termii_sender_id", "NECOMCSVOTE") or "NECOMCSVOTE"
        message_text = f"Your NECO MCS OTP for {purpose_label} is: {otp_code}. It is valid for {settings.otp_expire_minutes} minutes. Do not share this code."
        
        url = getattr(settings, "termii_url", "https://api.ng.termii.com/api/sms/send")
        payload = {
            "to": clean_phone,
            "from": sender_id,
            "sms": message_text,
            "type": "plain",
            "channel": "generic",
            "api_key": termii_api_key,
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json() if resp.status_code in (200, 201) else {}

            if resp.status_code in (200, 201) and (data.get("code") == "ok" or data.get("message") == "Successfully Sent"):
                logger.info(f"Termii OTP SMS sent successfully to {clean_phone} via sender '{sender_id}'")
                return True
            
            # If sender ID is still awaiting telecom approval, Termii returns 422 SENDER_ID_NOT_APPROVED
            if resp.status_code == 422 and "SENDER_ID_NOT_APPROVED" in str(resp.text):
                logger.warning(f"Termii sender ID '{sender_id}' is pending approval from telecom carriers: {resp.text}")
                print(f"\n========================================\n[TERMII SMS OTP - SENDER_ID PENDING APPROVAL]\nTo: {clean_phone}\nSender: {sender_id}\nCode: {otp_code}\nNote: Once Termii approves '{sender_id}', live SMS will deliver automatically.\n========================================\n")
                return True
            else:
                logger.error(f"Termii SMS delivery failed (HTTP {resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Error calling Termii SMS API: {e}")

    # 2. Twilio Fallback (if Twilio credentials are provided)
    if settings.twilio_account_sid and not settings.twilio_account_sid.startswith("your_"):
        try:
            from twilio.rest import Client
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            message = client.messages.create(
                body=f"Your NECO MCS OTP is: {otp_code}. It expires in {settings.otp_expire_minutes} minutes. Do not share it.",
                from_=settings.twilio_phone_number,
                to=f"+{clean_phone}" if not clean_phone.startswith("+") else clean_phone,
            )
            logger.info(f"Twilio OTP SMS sent to {clean_phone}, SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Twilio OTP SMS to {clean_phone}: {e}")

    # If in development and no provider delivered, print to console for testing
    if getattr(settings, "environment", "development") == "development":
        print(f"\n[DEV FALLBACK SMS OTP] To: {clean_phone} Code: {otp_code}\n")
        return True

    return False
