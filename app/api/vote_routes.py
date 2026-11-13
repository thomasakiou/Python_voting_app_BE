from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from ..domain.vote import Vote
from ..domain.office import Office
from ..core.database import get_db
from ..core.config import settings
from ..application.commands.vote.create_vote import CastVoteCommand, CastVoteHandler
from ..application.queries.vote.get_all_votes import ListVotesHandler, ListVotesQuery
from ..application.queries.vote.get_voter_by_username import GetVoterByCodeHandler, GetVoterByCodeQuery
from ..application.queries.vote.get_voters_by_id import GetVoterByIdHandler, GetVoterByIdQuery
from ..application.queries.vote.get_votes_by_cand_code import GetVoterByCandidateCodeHandler, GetVoterByCandidateCodeQuery
from ..core import database, oauth2
from ..schemas.vote import VoteCreate, VoteResponse, MyVoteResponse

router = APIRouter(prefix=f"{settings.api_prefix}/votes", tags=["Votes"])


# ============================================================
# CAST VOTE (VOTER ONLY)
# ============================================================
@router.post("/", response_model=VoteResponse)
def cast_vote(
    vote: VoteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["voter"])),
):
    command = CastVoteCommand(
        user_id=current_user.id,
        candidate_code=vote.candidate_code,
        candidate_codes=vote.candidate_codes,
        office_code=vote.office_code,
    )
    handler = CastVoteHandler(db)
    return handler.handle(command)


# ============================================================
# VOTER'S OWN VOTES & STATS (VOTER ONLY)
# ============================================================
@router.get("/my-votes", response_model=List[MyVoteResponse])
def get_my_votes(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["voter"])),
):
    """
    Returns only the authenticated voter's cast votes and receipts.
    Ensures voters cannot view other voters' ballots.
    """
    votes = (
        db.query(Vote)
        .filter(Vote.user_id == current_user.id)
        .order_by(Vote.created_at.desc())
        .all()
    )
    return votes


@router.get("/my-stats")
def get_my_stats(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["voter"])),
):
    """
    Returns voter progress statistics (e.g. voted 4 of 6 offices).
    """
    total_offices = db.query(Office).filter(Office.is_disqualified == False).count()
    user_votes = db.query(Vote).filter(Vote.user_id == current_user.id).all()
    voted_office_codes = list(set([v.office_code for v in user_votes]))

    return {
        "voter_name": current_user.full_name,
        "username": current_user.username,
        "total_offices": total_offices,
        "voted_count": len(voted_office_codes),
        "remaining_count": max(0, total_offices - len(voted_office_codes)),
        "is_completed": len(voted_office_codes) >= total_offices and total_offices > 0,
        "voted_office_codes": voted_office_codes,
        "votes": [
            {
                "office_code": v.office_code,
                "office_name": v.office_name,
                "candidate_name": v.candidate_name,
                "candidate_code": v.candidate_code,
                "receipt_hash": v.receipt_hash,
                "created_at": v.created_at,
            }
            for v in user_votes
        ],
    }


# ============================================================
# ADMIN: LIVE VOTES FEED WITH PAGINATION
# ============================================================
@router.get("/live")
def get_live_votes_summary(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Returns live vote counter and paginated cast votes for the admin live dashboard.
    Scales smoothly even with thousands or tens of thousands of cast ballots.
    """
    total_votes = db.query(Vote).count()
    offset = (page - 1) * page_size
    recent_votes = (
        db.query(Vote)
        .options(joinedload(Vote.user))
        .order_by(Vote.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {
        "total_votes_cast": total_votes,
        "total_items": total_votes,
        "page": page,
        "page_size": page_size,
        "recent_votes": [
            {
                "id": v.id,
                "username": v.user.username if v.user else v.user_name,
                "user_name": v.user.username if v.user else v.user_name,
                "full_name": v.user.full_name if v.user else v.user_name,
                "office_name": v.office_name,
                "candidate_name": v.candidate_name,
                "receipt_hash": v.receipt_hash,
                "created_at": v.created_at,
            }
            for v in recent_votes
        ],
    }


# ============================================================
# GET ALL VOTES (ADMIN ONLY)
# ============================================================
@router.get("/", response_model=List[VoteResponse])
def get_all_votes(
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    query = ListVotesQuery()
    handler = ListVotesHandler(db)
    return handler.handle(query)


# ============================================================
# GET VOTES BY USER ID (ADMIN ONLY)
# ============================================================
@router.get("/{userId}", response_model=List[VoteResponse])
def get_vote_by_user_id(
    userId: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    if userId:
        query = GetVoterByIdQuery(userId=userId)
        handler = GetVoterByIdHandler(db)
        return handler.handle(query)
    return db.query(Vote).all()


# ============================================================
# GET VOTES BY USERNAME (ADMIN ONLY)
# ============================================================
@router.get("/username/{username}", response_model=List[VoteResponse])
def get_vote_by_user(
    username: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    query = GetVoterByCodeQuery(username=username)
    handler = GetVoterByCodeHandler(db)
    return handler.handle(query)


# ============================================================
# GET VOTES BY CANDIDATE CODE (ADMIN ONLY)
# ============================================================
@router.get("/code/{code}", response_model=List[VoteResponse])
def get_vote_by_code(
    code: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    query = GetVoterByCandidateCodeQuery(candCode=code)
    handler = GetVoterByCandidateCodeHandler(db)
    return handler.handle(query)
