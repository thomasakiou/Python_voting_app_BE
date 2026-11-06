from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import io
import csv

from ..core import database, oauth2
from ..core.config import settings
from ..core.database import get_db
from ..core.cache import cache
from ..domain.vote import Vote
from ..domain.office import Office
from ..domain.candidate import Candidate
from ..application.queries.vote.count_all_votes import CountVotesQuery, CountVotesHandler

router = APIRouter(prefix=f"{settings.api_prefix}/results", tags=["Results"])


# ============================================================
# GET RESULTS FOR SPECIFIC OFFICE
# ============================================================
@router.get("/{office_code}")
def count_votes(
    office_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin", "voter"])),
):
    cache_key = f"results_{office_code}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    query = CountVotesQuery(office_code=office_code)
    handler = CountVotesHandler(db)
    results = handler.handle(query)

    response_data = {
        "office_code": office_code,
        "results": results,
    }
    cache.set(cache_key, response_data, ttl_seconds=5)
    return response_data


# ============================================================
# EXPORT VOTERS / VOTES BY OFFICE (CSV) - REQUIREMENT 5
# ============================================================
@router.get("/export/{office_code}")
def export_office_voters(
    office_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"])),
):
    """
    Download a CSV list of all voters who cast votes for a specific office/category.
    """
    office = db.query(Office).filter(Office.office_code == office_code).first()
    office_name = office.description if office else office_code

    votes = (
        db.query(Vote)
        .filter(Vote.office_code == office_code)
        .order_by(Vote.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Vote ID",
        "Voter MCS Username",
        "Voter Full Name",
        "Office Code",
        "Office Description",
        "Candidate Code",
        "Candidate Name",
        "Receipt Hash",
        "Date Voted"
    ])

    for v in votes:
        username = v.user.username if v.user else v.user_name
        writer.writerow([
            v.id,
            username,
            v.user_name,
            v.office_code,
            v.office_name,
            v.candidate_code,
            v.candidate_name,
            v.receipt_hash or "N/A",
            v.created_at.strftime("%Y-%m-%d %H:%M:%S") if v.created_at else ""
        ])

    csv_content = output.getvalue()
    filename = f"votes_office_{office_code}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
