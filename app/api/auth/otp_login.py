from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from ...core import database, oauth2
from ...core.config import settings
from ...core.otp_utils import (
    generate_otp,
    get_otp_expiry,
    send_otp_email,
    send_otp_sms,
    mask_email,
    mask_phone,
)
from ...domain import user as user_models
from ...domain import otp as otp_models
from ...domain import voting_time as vt_models
from ...schemas import otp as otp_schemas, token as token_schemas

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Election Login"])


# ============================================================
# STEP 1 – ELECTION LOGIN (username/MCS number → send 6-digit OTP)
# ============================================================
@router.post("/login", status_code=status.HTTP_200_OK)
@router.post("/election/login", status_code=status.HTTP_200_OK)
def initiate_login(
    credentials: otp_schemas.LoginRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """
    On election day, voter enters their 4-digit MCS username and clicks validate.
    Verifies eligibility, checks active election status, and sends a 6-digit OTP
    to their registered email with header 'NECO MCS Voting'.
    """
    username = credentials.username.strip()

    # 1. Look up user by username
    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter with MCS number '{username}' not found. Please verify your number.",
        )

    # 2. Only voters use this endpoint
    if user.role in ("admin", "super-admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators must log in via /admin/login using username and password.",
        )

    # 3. Check voter eligibility / active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have been disqualified / Your account has been disabled. Please contact the administrator.",
        )

    # 4. Check if voter has accredited
    if not user.is_accredited:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not accredited for this election. Please complete voter accreditation first at /accreditation.",
        )

    # 4b. Enforce Device Binding: Voter MUST vote from the device used for accreditation
    if user.accredited_device_id:
        client_device_id = (credentials.device_id or "").strip()
        if not client_device_id or client_device_id != user.accredited_device_id:
            device_desc = user.device_info or "the device used during accreditation"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Device Authorization Error: You can only vote using the specific device ({device_desc}) used during your voter accreditation.",
            )

    # 5. Check user email
    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No registered email address found for your profile. Please contact the administrator.",
        )

    # 6. Check if election is open / voting has started
    voting_record = db.query(vt_models.VotingTime).first()
    if not voting_record or not voting_record.is_active or voting_record.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voting is currently closed. Voting has not yet started or has been stopped by the administrator.",
        )

    # 7. Invalidate existing unused voting OTPs for this user
    db.query(otp_models.OTP).filter(
        otp_models.OTP.user_id == user.id,
        otp_models.OTP.purpose == "voting",
        otp_models.OTP.is_used == False,  # noqa: E712
    ).update({"is_used": True})
    db.commit()

    # 8. Generate 6-digit OTP and persist
    otp_code = generate_otp(6)
    otp_entry = otp_models.OTP(
        user_id=user.id,
        otp_code=otp_code,
        purpose="voting",
        expires_at=get_otp_expiry(settings.otp_expire_minutes),
        is_used=False,
    )
    db.add(otp_entry)
    db.commit()

    # 9. Deliver OTP via BackgroundTasks with header 'NECO MCS Voting'
    background_tasks.add_task(
        send_otp_email,
        recipient_email=user.email,
        otp_code=otp_code,
        full_name=user.full_name,
        subject="NECO MCS Voting",
        purpose_label="Voting Login",
    )
    if user.phone:
        background_tasks.add_task(send_otp_sms, user.phone, otp_code)

    return {
        "message": f"A 6-digit OTP has been sent to your registered email ({mask_email(user.email)}). Please enter it to access your ballot.",
        "otp_sent": True,
        "masked_email": mask_email(user.email),
        "username": user.username,
        "full_name": user.full_name,
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
    username = payload.username.strip()
    otp_code = payload.otp_code.strip()

    # 1. Look up user
    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid username or OTP.",
        )

    # 2. Check account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have been disqualified / Your account has been disabled.",
        )

    # 3. Check user is accredited
    if not user.is_accredited:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be accredited to log in for voting.",
        )

    # 3b. Enforce Device Binding
    if user.accredited_device_id:
        client_device_id = (credentials.device_id or "").strip()
        if not client_device_id or client_device_id != user.accredited_device_id:
            device_desc = user.device_info or "the device used during accreditation"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Device Authorization Error: You can only vote using the specific device ({device_desc}) used during your voter accreditation.",
            )

    # 4. Check election status
    voting_record = db.query(vt_models.VotingTime).first()
    if not voting_record or not voting_record.is_active or voting_record.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voting has closed or is not currently open.",
        )

    # 5. Find the latest valid (unused) voting OTP for this user
    otp_entry = (
        db.query(otp_models.OTP)
        .filter(
            otp_models.OTP.user_id == user.id,
            otp_models.OTP.purpose == "voting",
            otp_models.OTP.is_used == False,  # noqa: E712
        )
        .order_by(otp_models.OTP.created_at.desc())
        .first()
    )

    if not otp_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP found. Please request a new one.",
        )

    # 6. Check expiry
    now = datetime.now(timezone.utc)
    otp_expires = otp_entry.expires_at
    if otp_expires.tzinfo is None:
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)

    if now > otp_expires:
        otp_entry.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one.",
        )

    # 7. Verify OTP code
    if otp_entry.otp_code != otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code.",
        )

    # 8. Mark OTP as used
    otp_entry.is_used = True
    db.commit()

    # 9. Issue JWT access token
    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id), "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "fullname": user.full_name,
        "username": user.username,
        "role": user.role,
    }
