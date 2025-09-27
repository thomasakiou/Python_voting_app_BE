from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import candidate as models

@dataclass(frozen=True)
class GetCandidateByCodeQuery:
    candidate_code: str

class GetCandidateByCodeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetCandidateByCodeQuery):
        candidate = self.db.query(models.Candidate).filter(models.Candidate.candidate_code.ilike(f"%{query.candidate_code}%")).first()
        if not candidate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        return candidate
