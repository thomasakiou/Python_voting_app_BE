from dataclasses import dataclass
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ....domain import candidate as models


@dataclass(frozen=True)
class GetCandidateByOfficeCodeQuery:
    office_code: str

class GetCandidateByOfficeCodeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetCandidateByOfficeCodeQuery):
        candidates = self.db.query(models.Candidate).filter(models.Candidate.office_code == query.office_code).all()
        if not candidates:
            raise HTTPException(status_code=404, detail=f"No candidates found for office_code {query.office_code}")
        return candidates




# from dataclasses import dataclass
# from fastapi import HTTPException, status
# from ....domain import candidate as models

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