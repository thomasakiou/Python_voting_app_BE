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
# SMS DELIVERY (Twilio)
# ============================================================

def send_otp_sms(phone_number: str, otp_code: str) -> bool:
    """Send OTP via Twilio SMS. Skips gracefully if Twilio is not configured."""
    if not phone_number:
        logger.warning("No phone number provided – skipping SMS OTP delivery.")
        return False

    # Skip if Twilio credentials are not configured
    if not settings.twilio_account_sid or settings.twilio_account_sid.startswith("your_"):
        logger.warning(f"Twilio credentials not configured – skipping SMS. [DEV OTP: {otp_code}]")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        message = client.messages.create(
            body=f"Your NECO MCS OTP is: {otp_code}. It expires in {settings.otp_expire_minutes} minutes. Do not share it.",
            from_=settings.twilio_phone_number,
            to=phone_number,
        )
        logger.info(f"OTP SMS sent to {phone_number}, SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP SMS to {phone_number}: {e}")
        return False
