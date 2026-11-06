from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import candidate as models

@dataclass(frozen=True)
class GetCandidateByIdQuery:
    id: int

class GetCandidateByIdHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetCandidateByIdQuery):
        user = self.db.query(models.Candidate).filter(models.Candidate.id == query.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        return user
