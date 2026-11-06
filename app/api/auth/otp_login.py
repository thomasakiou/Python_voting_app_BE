from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ...core import database, oauth2
from ...core.config import settings
from ...core.otp_utils import generate_otp, get_otp_expiry, send_otp_email, send_otp_sms
from ...domain import user as user_models
from ...domain import otp as otp_models
from ...schemas import otp as otp_schemas, token as token_schemas

router = APIRouter(tags=["Login"])


# ============================================================
# STEP 1 – INITIATE LOGIN (username + phone → send OTP)
# ============================================================
@router.post("/login", status_code=status.HTTP_200_OK)
def initiate_login(
    credentials: otp_schemas.LoginRequest,
    db: Session = Depends(database.get_db),
):
    """
    Accepts username + phone number.
    Validates the user, generates a 6-digit OTP, and delivers it
    via SMS (to the registered phone) and Email (if email is set).
    """
    # ── 1. Look up the user by username
    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == credentials.username)
        .first()
    )
    if not user:
        # Generic message to avoid username enumeration
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials",
        )

    # ── 2. Ensure only voters use this endpoint (admins use POST /admin/login)
    if user.role in ("admin", "super-admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators must log in via /admin/login using username and password.",
        )

    # ── 3. Verify the supplied phone matches what is on file
    if not user.phone or user.phone.strip() != credentials.phone.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials",
        )

    # ── 3. Check the account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is deactivated. Please contact the administrator.",
        )

    # ── 4. Invalidate any existing unused OTPs for this user
    db.query(otp_models.OTP).filter(
        otp_models.OTP.user_id == user.id,
        otp_models.OTP.is_used == False,  # noqa: E712
    ).update({"is_used": True})
    db.commit()

    # ── 5. Generate OTP and persist it
    otp_code = generate_otp()
    otp_entry = otp_models.OTP(
        user_id=user.id,
        otp_code=otp_code,
        expires_at=get_otp_expiry(settings.otp_expire_minutes),
        is_used=False,
    )
    db.add(otp_entry)
    db.commit()

    # ── 6. Deliver OTP via SMS and/or Email
    sms_sent = send_otp_sms(user.phone, otp_code)
    email_sent = send_otp_email(user.email, otp_code, user.full_name) if user.email else False

    if not sms_sent and not email_sent:
        # At least one channel must succeed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deliver OTP. Please try again later.",
        )

    return {
        "message": "OTP sent to your registered phone number"
        + (" and email" if email_sent else "")
        + ". Please enter it to complete login.",
        "otp_sent": True,
    }


# ============================================================
# STEP 2 – VERIFY OTP → receive JWT token
# ============================================================
@router.post("/verify-otp", response_model=token_schemas.Token)
def verify_otp(
    payload: otp_schemas.VerifyOTPRequest,
    db: Session = Depends(database.get_db),
):
    """
    Accepts username + OTP code.
    If valid and not expired, returns a JWT access token.
    """
    # ── 1. Look up the user
    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == payload.username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid OTP or username",
        )

    # ── 2. Check account is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is deactivated.",
        )

    # ── 3. Find the latest valid (unused) OTP for this user
    otp_entry = (
        db.query(otp_models.OTP)
        .filter(
            otp_models.OTP.user_id == user.id,
            otp_models.OTP.is_used == False,  # noqa: E712
        )
        .order_by(otp_models.OTP.created_at.desc())
        .first()
    )

    if not otp_entry:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active OTP found. Please request a new one.",
        )

    # ── 4. Check expiry
    now = datetime.now(timezone.utc)
    otp_expires = otp_entry.expires_at
    # Make timezone-aware if it's naive (PostgreSQL may return naive datetimes)
    if otp_expires.tzinfo is None:
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)

    if now > otp_expires:
        otp_entry.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP has expired. Please request a new one.",
        )

    # ── 5. Verify OTP code
    if otp_entry.otp_code != payload.otp_code.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid OTP code.",
        )

    # ── 6. Mark OTP as used
    otp_entry.is_used = True
    db.commit()

    # ── 7. Issue JWT access token
    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id), "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "fullname": user.full_name,
    }
