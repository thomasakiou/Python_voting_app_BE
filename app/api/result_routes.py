# api/vote_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core import database, oauth2
from ..core.config import settings
from ..core.database import get_db
from ..application.queries.vote.count_all_votes import CountVotesQuery, CountVotesHandler
# from application.query_bus import QueryBus

router = APIRouter(prefix=f"{settings.api_prefix}/results", tags=["Results"])

@router.get("/{office_code}")
def count_votes(
    office_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.role_required(["super-admin", "admin"]))
):
    query = CountVotesQuery(office_code=office_code)
    handler = CountVotesHandler(db)
    results = handler.handle(query)

    return {
        "office_code": office_code,
        "results": results
    }
