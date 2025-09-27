# api/vote_router.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.domain.vote import Vote
from ..core.database import get_db
from ..core.config import settings
from ..application.commands.vote.create_vote import CastVoteCommand
from ..application.commands.vote.create_vote import CastVoteHandler
from ..application.queries.vote.get_all_votes import ListVotesHandler, ListVotesQuery
from ..application.queries.vote.get_voter_by_username import GetVoterByCodeHandler, GetVoterByCodeQuery
from ..application.queries.vote.get_voters_by_id import GetVoterByIdHandler, GetVoterByIdQuery
from ..core import database, oauth2
from ..schemas.vote import VoteCreate, VoteResponse

router = APIRouter(prefix=f"{settings.api_prefix}/votes", tags=["Votes"])


# ==========================
# CAST VOTE
# ==========================
@router.post("/", response_model= VoteResponse)
def cast_vote(
    vote: VoteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["voter"]))
):
    command = CastVoteCommand(
        user_id=current_user.id,
        candidate_code=vote.candidate_code,
        office_code=vote.office_code
    )
    handler = CastVoteHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL VOTES
# ==========================
@router.get("/", response_model=list[VoteResponse])
def get_all_votes(db: Session = Depends(get_db),
                  current_user=Depends(oauth2.role_required(["super-admin", "admin"]))):
    query = ListVotesQuery()
    handler = ListVotesHandler(db)
    return handler.handle(query)



# ==========================
# GET VOTES BY USER ID
# ==========================
@router.get("/{userId}", response_model=list[VoteResponse])
def get_vote_by_user_id(userId: int, db: Session = Depends(get_db), current_user=Depends(oauth2.role_required(["super-admin", "admin"]))):
        if userId:
            query = GetVoterByIdQuery(userId=userId)
            handler = GetVoterByIdHandler(db)
            return handler.handle(query)
        # Return all votes if no userId
        return db.query(Vote).all()



# ==========================
# GET VOTES BY USERNAME
# ==========================
@router.get("/{username}", response_model=list[VoteResponse])
def get_vote_by_user(username: str, db: Session = Depends(get_db), current_user=Depends(oauth2.role_required(["super-admin", "admin"]))):
    query = GetVoterByCodeQuery(username=username)
    handler = GetVoterByCodeHandler(db)
    return handler.handle(query)


