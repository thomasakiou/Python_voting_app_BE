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
                Candidate.image_url.label("image_url"),
                Candidate.mcs_number.label("mcs_number"),
                Candidate.file_no.label("file_no"),
                Candidate.conraiss.label("conraiss"),
                Candidate.station.label("station"),
                Office.description.label("office_name"),
                func.count(Vote.id).label("vote_count")
            )
            .join(Vote, Candidate.candidate_code == Vote.candidate_code, isouter=True)
            .join(Office, Candidate.office_code == Office.office_code)
            .filter(Candidate.office_code == query.office_code, Candidate.is_hidden == False)
            .group_by(
                Candidate.candidate_code,
                Candidate.name,
                Candidate.office_code,
                Candidate.image_url,
                Candidate.mcs_number,
                Candidate.file_no,
                Candidate.conraiss,
                Candidate.station,
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
                "image_url": r.image_url,
                "mcs_number": r.mcs_number or r.candidate_code,
                "file_no": r.file_no,
                "conraiss": r.conraiss,
                "station": r.station,
            }
            for r in results
        ]
