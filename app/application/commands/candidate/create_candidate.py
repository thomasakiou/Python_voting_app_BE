from dataclasses import dataclass
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from ....domain import candidate as models, office as model


@dataclass(frozen=True)
class CreateCandidateCommand:
    candidate_code: str
    name: str
    office_code: str
    image_url: Optional[str] = None
    manifesto_title: Optional[str] = None
    manifesto: Optional[str] = None
    mcs_number: Optional[str] = None
    conraiss: Optional[str] = None
    station: Optional[str] = None
    file_no: Optional[str] = None


class CreateCandidateHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: CreateCandidateCommand):
        clean_code = command.candidate_code.strip()
        existing = self.db.query(models.Candidate).filter(
            func.lower(models.Candidate.candidate_code) == func.lower(clean_code)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Candidate with code '{clean_code}' already exists ({existing.name})",
            )

        clean_file = command.file_no.strip() if command.file_no and command.file_no.strip() else None
        if clean_file:
            existing_file = self.db.query(models.Candidate).filter(
                func.lower(models.Candidate.file_no) == func.lower(clean_file)
            ).first()
            if existing_file:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Staff File Number '{clean_file}' is already assigned to candidate '{existing_file.name}' (#{existing_file.candidate_code})",
                )

        office_check = self.db.query(model.Office).filter(
            func.lower(model.Office.office_code) == func.lower(command.office_code.strip())
        ).first()
        if not office_check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Office: {command.office_code} is not a valid office")
        
        new_candidate = models.Candidate(
            candidate_code=clean_code, 
            name=command.name.strip(),
            office_code=command.office_code.strip(),
            image_url=command.image_url,
            manifesto_title=command.manifesto_title,
            manifesto=command.manifesto,
            mcs_number=command.mcs_number,
            conraiss=command.conraiss,
            station=command.station,
            file_no=clean_file,
        )
        self.db.add(new_candidate)
        self.db.commit()
        self.db.refresh(new_candidate)
        return new_candidate
