from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core import database, oauth2
from ..schemas import voting_time as schemas
from ..core.config import settings
from ..core.database import get_db
from ..application.commands.voting_time.set_voting_time import SetVotingTimeCommand, SetVotingTimeHandler
from ..application.queries.voting_time.get_voting_time import GetVotingTimeQuery, GetVotingTimeHandler
from datetime import datetime, timezone


router = APIRouter(prefix=f"{settings.api_prefix}/voting-time", tags=["Voting Time"])


# ==========================
# SET/UPDATE VOTING TIME
# ==========================
@router.post("/", response_model=schemas.VotingTimeResponse)
def set_voting_time(
    voting_time: schemas.VotingTimeCreate, 
    db: Session = Depends(database.get_db),
    current_user=Depends(oauth2.role_required(["super-admin"]))
):
    """
    Create or update voting time configuration.
    Only super-admin can access this endpoint.
    """
    command = SetVotingTimeCommand(
        start_time=voting_time.start_time,
        end_time=voting_time.end_time
    )
    handler = SetVotingTimeHandler(db)
    return handler.handle(command)


# ==========================
# GET VOTING TIME
# ==========================
@router.get("/", response_model=schemas.VotingTimeOut)
def get_voting_time(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"]))
):
    """
    Get current voting time configuration.
    All authenticated users can access this endpoint.
    """
    query = GetVotingTimeQuery()
    handler = GetVotingTimeHandler(db)
    voting_time = handler.handle(query)
    
    # Calculate is_active and time_remaining
    now = datetime.now(timezone.utc)
    
    # Make start_time and end_time timezone-aware if they aren't already
    start_time = voting_time.start_time
    end_time = voting_time.end_time
    
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    is_active = start_time <= now <= end_time
    time_remaining = None
    
    if is_active:
        time_remaining = int((end_time - now).total_seconds())
    
    return schemas.VotingTimeOut(
        id=voting_time.id,
        start_time=voting_time.start_time,
        end_time=voting_time.end_time,
        created_at=voting_time.created_at,
        updated_at=voting_time.updated_at,
        is_active=is_active,
        time_remaining=time_remaining
    )
