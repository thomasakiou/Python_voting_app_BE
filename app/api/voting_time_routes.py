from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..core import database, oauth2
from ..schemas import voting_time as schemas
from ..core.config import settings
from ..core.database import get_db
from ..core.cache import cache
from ..core.audit import record_audit_log
from ..domain import voting_time as vt_models

router = APIRouter(prefix=f"{settings.api_prefix}/voting-time", tags=["Voting Time"])


def get_or_create_voting_time(db: Session) -> vt_models.VotingTime:
    record = db.query(vt_models.VotingTime).first()
    if not record:
        record = vt_models.VotingTime(
            is_active=False,
            status="NOT_STARTED",
            start_time=None,
            end_time=None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


# ============================================================
# PUBLIC / VOTER STATUS CHECK
# ============================================================
@router.get("/status", response_model=schemas.VotingTimeOut)
def check_voting_status(db: Session = Depends(get_db)):
    """
    Public endpoint to check if election voting is active, scheduled, or stopped.
    Cached for high concurrency.
    """
    cached_status = cache.get("voting_status")
    if cached_status:
        return cached_status

    record = get_or_create_voting_time(db)
    now = datetime.now(timezone.utc)

    # If scheduled end_time passed, auto-mark stopped
    if record.end_time and record.is_active:
        end_time = record.end_time
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        if now > end_time:
            record.is_active = False
            record.status = "STOPPED"
            db.commit()

    time_remaining = None
    if record.is_active and record.end_time:
        end_time = record.end_time
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        time_remaining = max(0, int((end_time - now).total_seconds()))

    out = schemas.VotingTimeOut(
        id=record.id,
        start_time=record.start_time,
        end_time=record.end_time,
        created_at=record.created_at,
        updated_at=record.updated_at,
        is_active=record.is_active,
        status=record.status,
        time_remaining=time_remaining,
        message="Voting is currently in progress." if record.is_active else "Voting is closed.",
    )
    cache.set("voting_status", out, ttl_seconds=3)
    return out


# ============================================================
# ADMIN START VOTING BUTTON
# ============================================================
@router.post("/start", response_model=schemas.VotingTimeOut)
def start_voting(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Start voting immediately. Only when voting is started can voters log in and vote.
    """
    record = get_or_create_voting_time(db)
    now = datetime.now(timezone.utc)

    record.is_active = True
    record.status = "ACTIVE"
    record.start_time = now
    db.commit()
    db.refresh(record)

    cache.delete("voting_status")

    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="START_VOTING",
        target_type="ELECTION",
        details="Admin started voting session.",
        admin_id=current_user.id,
    )

    return schemas.VotingTimeOut(
        id=record.id,
        start_time=record.start_time,
        end_time=record.end_time,
        created_at=record.created_at,
        updated_at=record.updated_at,
        is_active=True,
        status="ACTIVE",
        message="Voting has been started successfully. Voters can now cast their votes.",
    )


# ============================================================
# ADMIN STOP VOTING BUTTON
# ============================================================
@router.post("/stop", response_model=schemas.VotingTimeOut)
def stop_voting(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Stop voting immediately. When clicked, voting stops immediately; no one can vote anymore.
    """
    record = get_or_create_voting_time(db)
    now = datetime.now(timezone.utc)

    record.is_active = False
    record.status = "STOPPED"
    record.end_time = now
    db.commit()
    db.refresh(record)

    cache.delete("voting_status")

    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="STOP_VOTING",
        target_type="ELECTION",
        details="Admin stopped voting session immediately.",
        admin_id=current_user.id,
    )

    return schemas.VotingTimeOut(
        id=record.id,
        start_time=record.start_time,
        end_time=record.end_time,
        created_at=record.created_at,
        updated_at=record.updated_at,
        is_active=False,
        status="STOPPED",
        message="Voting has been stopped immediately. No further votes can be cast.",
    )


# ============================================================
# GET CURRENT VOTING TIME (AUTHENTICATED)
# ============================================================
@router.get("/", response_model=schemas.VotingTimeOut)
def get_voting_time(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"])),
):
    return check_voting_status(db)


# ============================================================
# SET SCHEDULED VOTING TIME
# ============================================================
@router.post("/", response_model=schemas.VotingTimeResponse)
def set_voting_time(
    voting_time: schemas.VotingTimeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    record = get_or_create_voting_time(db)
    record.start_time = voting_time.start_time
    record.end_time = voting_time.end_time
    db.commit()
    db.refresh(record)

    cache.delete("voting_status")

    record_audit_log(
        db=db,
        admin_username=current_user.username,
        action="SET_VOTING_TIME",
        target_type="ELECTION",
        details=f"Scheduled voting start: {voting_time.start_time}, end: {voting_time.end_time}",
        admin_id=current_user.id,
    )

    return schemas.VotingTimeResponse(
        id=record.id,
        start_time=record.start_time,
        end_time=record.end_time,
        is_active=record.is_active,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
