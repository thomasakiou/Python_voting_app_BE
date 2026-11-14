from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from ..domain.vote import Vote
from ..domain.office import Office
from ..domain.user import User
from ..domain.voting_time import VotingTime
from ..application.queries.vote.count_all_votes import CountVotesQuery, CountVotesHandler
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
# CONTESTANTS' AGENTS / OBSERVER: ANONYMIZED LIVE MONITOR
# ============================================================
@router.get("/agents/live")
@router.get("/observer/live")
def get_agents_live_monitor(
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "agent"])),
):
    """
    Public / Agent live monitoring view.
    Provides complete live transparency into the election process while
    strictly protecting voter secrecy: NO voter names, NO MCS numbers, NO IDs.
    """
    # 1. Total Votes & Accreditation
    total_votes = db.query(Vote).count()
    total_voters = db.query(User).filter(User.role == "voter").count()
    accredited_count = db.query(User).filter(User.role == "voter", User.is_accredited == True).count()

    # 2. Voting Status & Window
    voting_time = db.query(VotingTime).first()
    is_active = voting_time.is_active if voting_time else False
    status_label = voting_time.status if voting_time else "NOT_STARTED"
    end_time = voting_time.end_time if voting_time else None

    # 3. Anonymized Recent Ballots (Zero Voter Identity)
    offset = (page - 1) * page_size
    recent_votes = (
        db.query(Vote)
        .order_by(Vote.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    anonymized_ballots = [
        {
            "id": v.id,
            "receipt_hash": v.receipt_hash or f"MCS-VERIFIED-{v.id:04d}",
            "office_name": v.office_name,
            "candidate_name": v.candidate_name,
            "created_at": v.created_at,
        }
        for v in recent_votes
    ]

    # 4. Office Results & Real-time Tallies
    offices = db.query(Office).filter(Office.is_disqualified == False).all()
    offices_results = []
    for off in offices:
        query = CountVotesQuery(office_code=off.office_code)
        handler = CountVotesHandler(db)
        cand_results = handler.handle(query)
        office_total = sum(c["vote_count"] for c in cand_results)
        offices_results.append({
            "office_code": off.office_code,
            "description": off.description,
            "max_votes": off.max_votes or 1,
            "total_votes": office_total,
            "candidates": cand_results,
        })

    turnout_pct = round((accredited_count / total_voters * 100), 1) if total_voters > 0 else 0.0

    return {
        "status": status_label,
        "is_active": is_active,
        "end_time": end_time,
        "total_votes_cast": total_votes,
        "total_voters": total_voters,
        "accredited_voters": accredited_count,
        "turnout_percentage": turnout_pct,
        "page": page,
        "page_size": page_size,
        "total_ballots": total_votes,
        "recent_ballots": anonymized_ballots,
        "offices_results": offices_results,
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
