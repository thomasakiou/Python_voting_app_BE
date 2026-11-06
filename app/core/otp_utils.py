import secrets
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone

from .config import settings

logger = logging.getLogger(__name__)


# ============================================================
# OTP GENERATION
# ============================================================

def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def get_otp_expiry(minutes: int = 10) -> datetime:
    """Return a timezone-aware expiry datetime."""
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


# ============================================================
# EMAIL DELIVERY
# ============================================================

def send_otp_email(recipient_email: str, otp_code: str, full_name: str) -> bool:
    """Send OTP to the user's email address via SMTP."""
    if not recipient_email:
        logger.warning("No email address provided – skipping email OTP delivery.")
        return False

    subject = "Your Voting Portal OTP Code"
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; padding: 20px;">
        <h2 style="color: #1a56db;">🗳️ Voting Portal – One-Time Password</h2>
        <p>Hello <strong>{full_name}</strong>,</p>
        <p>Your One-Time Password (OTP) to access the Voter Portal is:</p>
        <div style="background:#f0f4ff; border-left: 4px solid #1a56db; padding: 16px 24px; margin: 20px 0; border-radius: 4px;">
          <h1 style="letter-spacing: 12px; color: #1a56db; margin: 0;">{otp_code}</h1>
        </div>
        <p>This OTP is valid for <strong>10 minutes</strong>. Do not share it with anyone.</p>
        <p style="color: #888; font-size: 12px;">If you did not request this, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="color: #aaa; font-size: 11px;">Voting Portal – Secure Electronic Voting System</p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_sender_email, recipient_email, msg.as_string())
        logger.info(f"OTP email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {recipient_email}: {e}")
        return False


# ============================================================
# SMS DELIVERY (Twilio)
# ============================================================

def send_otp_sms(phone_number: str, otp_code: str) -> bool:
    """Send OTP via Twilio SMS. Skips gracefully if Twilio is not configured."""
    if not phone_number:
        logger.warning("No phone number provided – skipping SMS OTP delivery.")
        return False

    # Skip if Twilio credentials are not configured
    if not settings.twilio_account_sid or settings.twilio_account_sid.startswith("your_"):
        logger.warning("Twilio credentials not configured – skipping SMS OTP delivery.")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        message = client.messages.create(
            body=f"Your Voting Portal OTP is: {otp_code}. It expires in 10 minutes. Do not share it.",
            from_=settings.twilio_phone_number,
            to=phone_number,
        )
        logger.info(f"OTP SMS sent to {phone_number}, SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP SMS to {phone_number}: {e}")
        return False

