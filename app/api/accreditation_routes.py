from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from ..core import database
from ..core.config import settings
from ..core.otp_utils import generate_otp, get_otp_expiry, send_otp_email, send_otp_sms
from ..domain import user as user_models
from ..domain import otp as otp_models
from ..schemas import otp as otp_schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{settings.api_prefix}/accreditation", tags=["Accreditation"])


# ============================================================
# STEP 1: VALIDATE VOTER MCS NUMBER
# ============================================================
@router.post("/validate", response_model=otp_schemas.AccreditationValidateResponse)
def validate_voter_for_accreditation(
    payload: otp_schemas.AccreditationValidateRequest,
    db: Session = Depends(database.get_db),
):
    """
    Validate 4-digit MCS number. If user exists and is active, returns
    voter's full name to be displayed in an uneditable field for confirmation.
    """
    username = payload.username.strip()
    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter with MCS number '{username}' was not found in the voters register. Please verify your number.",
        )

    if user.role != "voter":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators do not require voter accreditation.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated / disqualified. You cannot accredit for this election. Please contact the administrator.",
        )

    if user.is_accredited:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Voter '{user.full_name}' is already accredited for the NECO MCS election. Please wait for election day to vote.",
        )

    return otp_schemas.AccreditationValidateResponse(
        username=user.username,
        full_name=user.full_name,
        is_accredited=user.is_accredited,
        is_active=user.is_active,
        phone=user.phone,
        email=user.email,
        message="Voter identity confirmed. Please enter your phone number and email to receive your OTP.",
    )


# ============================================================
# STEP 2: SUBMIT CONTACT & SEND OTP
# ============================================================
@router.post("/send-otp", status_code=status.HTTP_200_OK)
def send_accreditation_otp(
    payload: otp_schemas.AccreditationSendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """
    Accepts phone and email (both compulsory), generates OTP,
    and sends it to the user's email with header 'NECO MCS Accreditation'.
    Phone and email are NOT saved to the user table until OTP is verified.
    """
    username = payload.username.strip()
    phone = payload.phone.strip()
    email = payload.email.strip().lower()

    if not phone or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both phone number and email address are compulsory.",
        )

    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter with MCS number '{username}' not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated / disqualified. You cannot accredit for this election.",
        )

    if user.is_accredited:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already accredited for the NECO MCS election.",
        )

    # Invalidate previous unused accreditation OTPs for this user
    db.query(otp_models.OTP).filter(
        otp_models.OTP.user_id == user.id,
        otp_models.OTP.purpose == "accreditation",
        otp_models.OTP.is_used == False,  # noqa: E712
    ).update({"is_used": True})
    db.commit()

    # Generate 6-digit OTP
    otp_code = generate_otp(6)
    otp_entry = otp_models.OTP(
        user_id=user.id,
        otp_code=otp_code,
        purpose="accreditation",
        temp_email=email,
        temp_phone=phone,
        expires_at=get_otp_expiry(settings.otp_expire_minutes),
        is_used=False,
    )
    db.add(otp_entry)
    db.commit()

    # Deliver OTP with header "NECO MCS Accreditation"
    # Using background tasks ensures high throughput for 3000+ voters
    background_tasks.add_task(
        send_otp_email,
        recipient_email=email,
        otp_code=otp_code,
        full_name=user.full_name,
        subject="NECO MCS Accreditation",
        purpose_label="Accreditation",
    )
    if phone:
        background_tasks.add_task(send_otp_sms, phone, otp_code)

    return {
        "message": f"OTP has been dispatched to {email}. Please enter the OTP to complete accreditation.",
        "otp_sent": True,
        "expires_in_minutes": settings.otp_expire_minutes,
    }


# ============================================================
# STEP 3: VERIFY OTP AND FINALIZE ACCREDITATION
# ============================================================
@router.post("/verify-otp", status_code=status.HTTP_200_OK)
def verify_accreditation_otp(
    payload: otp_schemas.AccreditationVerifyOTPRequest,
    db: Session = Depends(database.get_db),
):
    """
    Verifies the accreditation OTP. Only after OTP validation are the
    user's phone and email fields populated and is_accredited set to True.
    """
    username = payload.username.strip()
    otp_code = payload.otp_code.strip()
    phone = payload.phone.strip()
    email = payload.email.strip().lower()

    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voter not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated / disqualified. You cannot accredit for this election.",
        )

    if user.is_accredited:
        return {
            "message": "You have been successfully accredited for the NECO MCS election, wait for further instruction for voting.",
            "accredited": True,
            "full_name": user.full_name,
            "username": user.username,
        }

    # Find latest valid accreditation OTP
    otp_entry = (
        db.query(otp_models.OTP)
        .filter(
            otp_models.OTP.user_id == user.id,
            otp_models.OTP.purpose == "accreditation",
            otp_models.OTP.is_used == False,  # noqa: E712
        )
        .order_by(otp_models.OTP.created_at.desc())
        .first()
    )

    if not otp_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active accreditation OTP found. Please request a new OTP code.",
        )

    # Check expiry
    now = datetime.now(timezone.utc)
    otp_expires = otp_entry.expires_at
    if otp_expires.tzinfo is None:
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)

    if now > otp_expires:
        otp_entry.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The accreditation OTP has expired. Please request a new code.",
        )

    # Verify code
    if otp_entry.otp_code != otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please check and try again.",
        )

    # Mark OTP as used
    otp_entry.is_used = True

    # NOW populate user phone, email, and accreditation status!
    user.phone = phone
    user.email = email
    user.is_accredited = True
    user.accredited_at = now
    db.commit()
    db.refresh(user)

    logger.info(f"Voter '{user.username}' successfully accredited with email '{user.email}'")

    return {
        "message": "you have been successfully accredited for the NECO MCS election, wait for further instruction for voting.",
        "accredited": True,
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
    }
