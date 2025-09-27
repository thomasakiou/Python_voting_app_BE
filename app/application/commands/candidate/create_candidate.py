from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import user as models
from ....core import utils, config
import csv
from fastapi import HTTPException, status
from ....domain import candidate as models, office as model
from ....core import utils
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CreateCandidateCommand:
    candidate_code: str
    name: str
    office_code: str


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
                            #    office_id=command.office_id,
                               candidate_code=command.candidate_code, 
                               name=command.name,
                               office_code=command.office_code
                                )
        self.db.add(new_candidate)
        self.db.commit()
        self.db.refresh(new_candidate)
        return new_candidate
    