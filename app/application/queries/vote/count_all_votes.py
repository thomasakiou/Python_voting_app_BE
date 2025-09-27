# application/queries/vote_queries.py
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from ....domain import Vote, Candidate, Office
from dataclasses import dataclass


@dataclass(frozen=True)
class CountVotesQuery:
    office_code: str


class CountVotesHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: "CountVotesQuery"):
        results = (
            self.db.query(
                Candidate.candidate_code.label("candidate_code"),
                Candidate.name.label("candidate_name"),
                Candidate.office_code,
                Office.description.label("office_name"),
                func.count(Vote.id).label("vote_count")
            )
            .join(Vote, Candidate.candidate_code == Vote.candidate_code, isouter=True)
            .join(Office, Candidate.office_code == Office.office_code)  # ✅ join office
            .filter(Candidate.office_code == query.office_code)
            .group_by(
                Candidate.candidate_code,
                Candidate.name,
                Candidate.office_code,
                Office.description
            )
            .all()
        )

        return [
            {
                "candidate_code": r.candidate_code,
                "candidate_name": r.candidate_name,
                "office_code": r.office_code,
                "office_name": r.office_name,   
                "vote_count": r.vote_count,
            }
            for r in results
        ]


