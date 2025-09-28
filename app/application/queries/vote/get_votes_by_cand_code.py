from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import vote as models

@dataclass(frozen=True)
class GetVoterByCandidateCodeQuery:
    candCode: str


class GetVoterByCandidateCodeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetVoterByCandidateCodeQuery):
        voter = self.db.query(models.Vote).filter(models.Vote.candidate_code.ilike(f"%{query.candCode}%")).all()
        if not voter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        return voter
