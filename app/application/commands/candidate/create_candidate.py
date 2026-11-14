from dataclasses import dataclass
from typing import Optional
from fastapi import HTTPException, status
from ....domain import candidate as models, office as model


@dataclass(frozen=True)
class CreateCandidateCommand:
    candidate_code: str
    name: str
    office_code: str
    image_url: Optional[str] = None
    manifesto_title: Optional[str] = None
    manifesto: Optional[str] = None


class CreateCandidateHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: CreateCandidateCommand):
        existing = self.db.query(models.Candidate).filter(
            models.Candidate.candidate_code.ilike(f"%{command.candidate_code}%")).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Candidate already exists")

        office_check = self.db.query(model.Office).filter(model.Office.office_code.ilike(f"%{command.office_code}%")).first()
        if not office_check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Office: {command.office_code} is not a valid office")
        
        new_candidate = models.Candidate(
            candidate_code=command.candidate_code, 
            name=command.name,
            office_code=command.office_code,
            image_url=command.image_url,
            manifesto_title=command.manifesto_title,
            manifesto=command.manifesto,
        )
        self.db.add(new_candidate)
        self.db.commit()
        self.db.refresh(new_candidate)
        return new_candidate
