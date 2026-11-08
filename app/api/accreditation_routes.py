from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from ..core import database
from ..core.config import settings
from ..core.otp_utils import (
    generate_otp,
    get_otp_expiry,
    send_otp_email,
    send_otp_sms,
    mask_email,
    mask_phone,
)
from ..domain import user as user_models
from ..domain import otp as otp_models
from ..domain.portal_lock import PortalLock
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
    lock = db.query(PortalLock).filter(PortalLock.id == 1).first()
    if lock and lock.is_accreditation_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=lock.accreditation_message or "Voter Accreditation is currently closed by the election administrator.",
        )

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

    # Check voter has at least one contact method (email OR phone)
    has_email = bool(user.email and user.email.strip())
    has_phone = bool(user.phone and user.phone.strip())
    if not has_email and not has_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No registered email or phone number found for voter '{user.full_name}' (MCS #{username}). Please register your contact details first at /contact-update.",
        )

    masked_email_val = mask_email(user.email) if has_email else "Not provided"
    masked_phone_val = mask_phone(user.phone) if has_phone else "Not provided"

    return otp_schemas.AccreditationValidateResponse(
        username=user.username,
        full_name=user.full_name,
        is_accredited=user.is_accredited,
        is_active=user.is_active,
        phone=masked_phone_val,
        email=masked_email_val,
        masked_phone=masked_phone_val,
        masked_email=masked_email_val,
        message="Voter identity confirmed. Please review your details and request your OTP.",
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
    Sends OTP to the voter's pre-registered email in the database.
    Does not accept arbitrary email input to prevent voter impersonation.
    """
    lock = db.query(PortalLock).filter(PortalLock.id == 1).first()
    if lock and lock.is_accreditation_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=lock.accreditation_message or "Voter Accreditation is currently closed by the election administrator.",
        )

    username = payload.username.strip()

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

    has_email = bool(user.email and user.email.strip())
    has_phone = bool(user.phone and user.phone.strip())
    if not has_email and not has_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No registered email or phone number found for voter '{user.full_name}'. Please register your contact details first at /contact-update.",
        )

    registered_email = user.email.strip().lower() if has_email else None
    registered_phone = user.phone.strip() if has_phone else None

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
        temp_email=registered_email,
        temp_phone=registered_phone,
        expires_at=get_otp_expiry(settings.otp_expire_minutes),
        is_used=False,
    )
    db.add(otp_entry)
    db.commit()

    # Deliver OTP: Send to Email if present, Phone if present, or BOTH if both present
    destinations = []
    if registered_email:
        background_tasks.add_task(
            send_otp_email,
            recipient_email=registered_email,
            otp_code=otp_code,
            full_name=user.full_name,
            subject="NECO MCS Accreditation",
            purpose_label="Accreditation",
        )
        destinations.append(f"email ({mask_email(registered_email)})")

    if registered_phone:
        background_tasks.add_task(
            send_otp_sms, 
            phone_number=registered_phone, 
            otp_code=otp_code,
            purpose_label="Accreditation",
        )
        destinations.append(f"phone ({mask_phone(registered_phone)})")

    dest_str = " and ".join(destinations) if destinations else "contact address"
    masked_e = mask_email(registered_email) if registered_email else None
    masked_p = mask_phone(registered_phone) if registered_phone else None

    return {
        "message": f"OTP has been dispatched to your registered {dest_str}. Please enter the OTP to complete accreditation.",
        "otp_sent": True,
        "expires_in_minutes": settings.otp_expire_minutes,
        "masked_email": masked_e,
        "masked_phone": masked_p,
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
    Verifies the accreditation OTP. Only marks user as accredited without
    allowing client to overwrite the registered contact information.
    """
    lock = db.query(PortalLock).filter(PortalLock.id == 1).first()
    if lock and lock.is_accreditation_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=lock.accreditation_message or "Voter Accreditation is currently closed by the election administrator.",
        )

    username = payload.username.strip()
    otp_code = payload.otp_code.strip()

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
            "email": mask_email(user.email),
            "phone": mask_phone(user.phone),
            "masked_email": mask_email(user.email),
            "masked_phone": mask_phone(user.phone),
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

    # Bind the voter to this physical device
    if payload.device_id:
        user.accredited_device_id = payload.device_id.strip()
    if payload.device_info:
        user.device_info = payload.device_info.strip()

    # Mark user as accredited
    user.is_accredited = True
    user.accredited_at = now
    db.commit()
    db.refresh(user)

    logger.info(f"Voter '{user.username}' successfully accredited and bound to device '{user.device_info or user.accredited_device_id}'")

    return {
        "message": "you have been successfully accredited for the NECO MCS election, wait for further instruction for voting.",
        "accredited": True,
        "full_name": user.full_name,
        "username": user.username,
        "email": mask_email(user.email),
        "phone": mask_phone(user.phone),
        "masked_email": mask_email(user.email),
        "masked_phone": mask_phone(user.phone),
        "device_info": user.device_info,
    }
