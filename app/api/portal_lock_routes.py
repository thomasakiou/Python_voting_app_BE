from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ..core import database, oauth2
from ..core.audit import record_audit_log
from ..core.config import settings
from ..domain.portal_lock import PortalLock
from ..schemas import portal_lock as schemas

router = APIRouter(prefix=f"{settings.api_prefix}/portal-locks", tags=["Portal Locks"])


def get_or_create_portal_locks(db: Session) -> PortalLock:
    lock = db.query(PortalLock).filter(PortalLock.id == 1).first()
    if not lock:
        lock = PortalLock(
            id=1,
            is_contact_update_locked=False,
            is_accreditation_locked=False,
            is_election_locked=False,
        )
        db.add(lock)
        db.commit()
        db.refresh(lock)
    return lock


@router.get("/status", response_model=schemas.PortalLockStatusResponse)
def get_portal_locks_status(db: Session = Depends(database.get_db)):
    """
    Public endpoint to check the lock status of Contact Update, Accreditation, and Election portals.
    """
    lock = get_or_create_portal_locks(db)
    return {
        "contact_update": {
            "is_locked": lock.is_contact_update_locked,
            "message": lock.contact_update_message or "The Voter Contact Update portal is currently closed by the election administrator.",
        },
        "accreditation": {
            "is_locked": lock.is_accreditation_locked,
            "message": lock.accreditation_message or "Voter Accreditation is currently closed by the election administrator.",
        },
        "election": {
            "is_locked": lock.is_election_locked,
            "message": lock.election_message or "The Election portal is currently closed by the election administrator.",
        },
        "updated_at": lock.updated_at,
    }


@router.post("/toggle", response_model=schemas.PortalLockStatusResponse)
def toggle_portal_lock(
    payload: schemas.PortalLockToggleRequest,
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Admin endpoint to toggle lock/unlock status of a voter portal.
    """
    lock = get_or_create_portal_locks(db)

    if payload.portal == "contact_update":
        lock.is_contact_update_locked = payload.is_locked
        if payload.message:
            lock.contact_update_message = payload.message
    elif payload.portal == "accreditation":
        lock.is_accreditation_locked = payload.is_locked
        if payload.message:
            lock.accreditation_message = payload.message
    elif payload.portal == "election":
        lock.is_election_locked = payload.is_locked
        if payload.message:
            lock.election_message = payload.message
    else:
        raise HTTPException(status_code=400, detail="Invalid portal specified.")

    db.commit()
    db.refresh(lock)

    action = "LOCK_PORTAL" if payload.is_locked else "UNLOCK_PORTAL"
    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action=action,
        target_type="PORTAL",
        target_id=payload.portal,
        details=f"Admin set portal '{payload.portal}' is_locked={payload.is_locked}",
        admin_id=current_user.id,
    )

    return get_portal_locks_status(db=db)
