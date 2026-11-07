from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional, List
import logging

from ..core import database, oauth2
from ..core.config import settings
from ..core.otp_utils import generate_otp, get_otp_expiry, send_otp_email, send_otp_sms, mask_email, mask_phone
from ..core.audit import record_audit_log
from ..core.cache import cache
from ..domain import user as user_models
from ..domain import otp as otp_models
from ..domain import dispute as dispute_models
from ..schemas import voter_contact as schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{settings.api_prefix}/voter-contact", tags=["Voter Contact Management"])


# ============================================================
# 1. VOTER CONTACT LOOKUP (BY MCS NUMBER)
# ============================================================
@router.post("/lookup", response_model=schemas.VoterContactLookupResponse)
def lookup_voter_contact(
    payload: schemas.VoterContactLookupRequest,
    db: Session = Depends(database.get_db),
):
    """
    Look up a voter by 4-digit MCS number.
    Returns voter's current contact info and flags indicating whether
    email and phone already exist (and are thus ineditable).
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
            detail=f"Voter with MCS number '{username}' not found in the voters register.",
        )

    if user.role != "voter":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators do not use this portal.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated / disqualified. Please contact the administrator.",
        )

    has_email = bool(user.email and user.email.strip())
    has_phone = bool(user.phone and user.phone.strip())

    return schemas.VoterContactLookupResponse(
        username=user.username,
        full_name=user.full_name,
        email=user.email if has_email else None,
        phone=user.phone if has_phone else None,
        masked_email=mask_email(user.email) if has_email else None,
        masked_phone=mask_phone(user.phone) if has_phone else None,
        has_email=has_email,
        has_phone=has_phone,
        is_accredited=user.is_accredited,
        is_active=user.is_active,
        message="Voter record loaded successfully.",
    )


# ============================================================
# 2. SEND OTP (FOR MISSING DETAILS OR EXISTING CONFIRMATION)
# ============================================================
@router.post("/send-otp", status_code=status.HTTP_200_OK)
def send_contact_otp(
    payload: schemas.VoterContactSendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    """
    Requests OTP for contact details verification.
    - If email/phone do not exist, validates the input for uniqueness across all users.
    - Data is NOT saved to the database at this point; it is temporarily stored with the OTP.
    - If email already exists, OTP is sent to the existing registered email.
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
            detail=f"Voter with MCS number '{username}' not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated / disqualified.",
        )

    # Determine target email and phone
    has_existing_email = bool(user.email and user.email.strip())
    new_email = str(payload.email).strip().lower() if payload.email and str(payload.email).strip() else None

    if has_existing_email:
        target_email = user.email.strip().lower()
    else:
        target_email = new_email
        if target_email:
            # UNIQUENESS CHECK: Ensure no two voters share the same email
            email_exists = (
                db.query(user_models.User)
                .filter(func.lower(user_models.User.email) == target_email, user_models.User.id != user.id)
                .first()
            )
            if email_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email address is already registered to another voter. Every email must be unique.",
                )

    has_existing_phone = bool(user.phone and user.phone.strip())
    new_phone = str(payload.phone).strip() if payload.phone and str(payload.phone).strip() else None

    if has_existing_phone:
        target_phone = user.phone.strip()
    else:
        target_phone = new_phone
        if target_phone:
            # UNIQUENESS CHECK: Ensure no two voters share the same phone number
            phone_exists = (
                db.query(user_models.User)
                .filter(user_models.User.phone == target_phone, user_models.User.id != user.id)
                .first()
            )
            if phone_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This phone number is already registered to another voter. Every phone number must be unique.",
                )

    # Ensure voter has at least one contact destination
    if not target_email and not target_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least an email address or a phone number to receive your OTP.",
        )

    # Invalidate prior unused contact_update OTPs for this user
    db.query(otp_models.OTP).filter(
        otp_models.OTP.user_id == user.id,
        otp_models.OTP.purpose == "contact_update",
        otp_models.OTP.is_used == False,  # noqa: E712
    ).update({"is_used": True})
    db.commit()

    # Generate 6-digit OTP
    otp_code = generate_otp(6)
    otp_entry = otp_models.OTP(
        user_id=user.id,
        otp_code=otp_code,
        purpose="contact_update",
        temp_email=target_email,
        temp_phone=target_phone,
        expires_at=get_otp_expiry(settings.otp_expire_minutes),
        is_used=False,
    )
    db.add(otp_entry)
    db.commit()

    # Deliver OTP: Send to Email if present, Phone if present, or BOTH if both present
    destinations = []
    if target_email:
        background_tasks.add_task(
            send_otp_email,
            recipient_email=target_email,
            otp_code=otp_code,
            full_name=user.full_name,
            subject="NECO MCS Contact Verification",
            purpose_label="Contact Verification",
        )
        destinations.append(f"email ({mask_email(target_email)})")

    if target_phone:
        background_tasks.add_task(
            send_otp_sms, 
            phone_number=target_phone, 
            otp_code=otp_code,
            purpose_label="Contact Verification",
        )
        destinations.append(f"phone ({mask_phone(target_phone)})")

    dest_str = " and ".join(destinations) if destinations else "contact address"

    return {
        "message": f"Verification OTP has been sent to your registered {dest_str}. Please enter it to confirm.",
        "otp_sent": True,
        "masked_email": mask_email(target_email) if target_email else None,
        "masked_phone": mask_phone(target_phone) if target_phone else None,
        "expires_in_minutes": settings.otp_expire_minutes,
    }


# ============================================================
# 3. VERIFY OTP AND SAVE CONTACT DETAILS TO DATABASE
# ============================================================
@router.post("/verify-otp", status_code=status.HTTP_200_OK)
def verify_contact_otp(
    payload: schemas.VoterContactVerifyOTPRequest,
    db: Session = Depends(database.get_db),
):
    """
    Verifies the OTP.
    ONLY after OTP is successfully verified are the new email and phone
    persisted into the database!
    """
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
            detail=f"Voter with MCS number '{username}' not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated / disqualified.",
        )

    # Find active contact_update OTP
    otp_entry = (
        db.query(otp_models.OTP)
        .filter(
            otp_models.OTP.user_id == user.id,
            otp_models.OTP.purpose == "contact_update",
            otp_models.OTP.is_used == False,  # noqa: E712
        )
        .order_by(otp_models.OTP.created_at.desc())
        .first()
    )

    if not otp_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification OTP found. Please request a new OTP code.",
        )

    # Expiry check
    now = datetime.now(timezone.utc)
    otp_expires = otp_entry.expires_at
    if otp_expires.tzinfo is None:
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)

    if now > otp_expires:
        otp_entry.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification OTP has expired. Please request a new code.",
        )

    # Code match check
    if otp_entry.otp_code != otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please check and try again.",
        )

    # Mark OTP as used
    otp_entry.is_used = True

    # FINAL UNIQUENESS & PERSISTENCE
    # Only update empty fields to preserve existing ones unless modified through dispute
    updated_fields = []
    if otp_entry.temp_email and not user.email:
        email_collision = (
            db.query(user_models.User)
            .filter(func.lower(user_models.User.email) == otp_entry.temp_email.lower(), user_models.User.id != user.id)
            .first()
        )
        if email_collision:
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email address was just registered by another voter. Please provide a different email.",
            )
        user.email = otp_entry.temp_email
        updated_fields.append("email")

    if otp_entry.temp_phone and not user.phone:
        phone_collision = (
            db.query(user_models.User)
            .filter(user_models.User.phone == otp_entry.temp_phone, user_models.User.id != user.id)
            .first()
        )
        if phone_collision:
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This phone number was just registered by another voter. Please provide a different phone.",
            )
        user.phone = otp_entry.temp_phone
        updated_fields.append("phone")

    db.commit()
    db.refresh(user)

    cache.delete("voter_analysis")

    logger.info(f"Voter '{user.username}' contact info verified. Updated fields: {updated_fields}")

    return {
        "message": "Your contact details have been verified and saved to the voters register.",
        "verified": True,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "masked_email": mask_email(user.email),
        "masked_phone": mask_phone(user.phone),
    }


# ============================================================
# 4. RAISE DISPUTE (FOR CHANGING EXISTING CONTACT INFO)
# ============================================================
@router.post("/dispute", response_model=schemas.VoterDisputeOut, status_code=status.HTTP_201_CREATED)
def raise_voter_dispute(
    payload: schemas.VoterDisputeCreateRequest,
    db: Session = Depends(database.get_db),
):
    """
    Allows a voter to raise a dispute regarding existing ineditable contact info
    (e.g., incorrect email, incorrect phone, lost access).
    The dispute is queued for admin investigation and action.
    """
    username = payload.username.strip()
    reason = payload.reason.strip()

    if not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A detailed reason or explanation is required to submit a dispute.",
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

    req_email = str(payload.requested_email).strip().lower() if payload.requested_email else None
    req_phone = str(payload.requested_phone).strip() if payload.requested_phone else None

    # Check uniqueness if requested_email is provided
    if req_email:
        email_collision = (
            db.query(user_models.User)
            .filter(func.lower(user_models.User.email) == req_email, user_models.User.id != user.id)
            .first()
        )
        if email_collision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The requested email address '{req_email}' is already in use by another voter account.",
            )

    # Check uniqueness if requested_phone is provided
    if req_phone:
        phone_collision = (
            db.query(user_models.User)
            .filter(user_models.User.phone == req_phone, user_models.User.id != user.id)
            .first()
        )
        if phone_collision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The requested phone number '{req_phone}' is already in use by another voter account.",
            )

    dispute = dispute_models.VoterDispute(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        current_email=user.email,
        current_phone=user.phone,
        requested_email=req_email,
        requested_phone=req_phone,
        dispute_type=payload.dispute_type or "CONTACT_UPDATE",
        reason=reason,
        status="PENDING",
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    logger.info(f"Dispute #{dispute.id} created by voter '{user.username}'")

    return dispute


# ============================================================
# 5. ADMIN: LIST ALL VOTER DISPUTES
# ============================================================
@router.get("/disputes", response_model=List[schemas.VoterDisputeOut])
def get_voter_disputes(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Admin endpoint to view all submitted voter disputes.
    """
    query = db.query(dispute_models.VoterDispute)
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(dispute_models.VoterDispute.status == status_filter.upper())
    return query.order_by(dispute_models.VoterDispute.created_at.desc()).all()


# ============================================================
# 6. ADMIN: RESOLVE / ACTION A VOTER DISPUTE
# ============================================================
@router.patch("/disputes/{dispute_id}/resolve", response_model=schemas.VoterDisputeOut)
def resolve_voter_dispute(
    dispute_id: int,
    payload: schemas.VoterDisputeResolveRequest,
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Admin reviews and resolves a voter dispute:
    - If action == 'APPROVE': updates voter's email and/or phone to requested values.
    - If action == 'REJECT': marks dispute as rejected with admin notes.
    """
    dispute = (
        db.query(dispute_models.VoterDispute)
        .filter(dispute_models.VoterDispute.id == dispute_id)
        .first()
    )

    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute #{dispute_id} not found.",
        )

    if dispute.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dispute #{dispute_id} has already been {dispute.status.lower()}.",
        )

    user = (
        db.query(user_models.User)
        .filter(user_models.User.id == dispute.user_id)
        .first()
    )

    action = payload.action.strip().upper()
    now = datetime.now(timezone.utc)

    if action == "APPROVE":
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated voter account no longer exists.",
            )

        # Apply requested email if provided
        if dispute.requested_email:
            # Recheck uniqueness
            coll = (
                db.query(user_models.User)
                .filter(func.lower(user_models.User.email) == dispute.requested_email.lower(), user_models.User.id != user.id)
                .first()
            )
            if coll:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot approve: Email '{dispute.requested_email}' is already taken by voter '{coll.username}'.",
                )
            user.email = dispute.requested_email

        # Apply requested phone if provided
        if dispute.requested_phone:
            coll_p = (
                db.query(user_models.User)
                .filter(user_models.User.phone == dispute.requested_phone, user_models.User.id != user.id)
                .first()
            )
            if coll_p:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot approve: Phone '{dispute.requested_phone}' is already taken by voter '{coll_p.username}'.",
                )
            user.phone = dispute.requested_phone

        dispute.status = "RESOLVED"
        record_audit_log(
            db=db,
            admin_username=current_user.username,
            action="APPROVE_VOTER_DISPUTE",
            target_type="VOTER_DISPUTE",
            target_id=str(dispute.id),
            details=f"Approved dispute #{dispute.id} for voter {user.username}. Updated contact details.",
            admin_id=current_user.id,
        )
    elif action == "REJECT":
        dispute.status = "REJECTED"
        record_audit_log(
            db=db,
            admin_username=current_user.username,
            action="REJECT_VOTER_DISPUTE",
            target_type="VOTER_DISPUTE",
            target_id=str(dispute.id),
            details=f"Rejected dispute #{dispute.id} for voter {dispute.username}. Notes: {payload.admin_notes or 'None'}",
            admin_id=current_user.id,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be either 'APPROVE' or 'REJECT'.",
        )

    dispute.admin_notes = payload.admin_notes
    dispute.resolved_by = current_user.username
    dispute.resolved_at = now

    db.commit()
    db.refresh(dispute)
    cache.delete("voter_analysis")

    return dispute
