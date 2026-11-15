from dataclasses import dataclass
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from ....domain import candidate as models, office as model

@dataclass(frozen=True)
class UpdateCandidateCommand:
    candidate_id: int
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

class UpdateCandidateHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: UpdateCandidateCommand):
        candidate_query = self.db.query(models.Candidate).filter(models.Candidate.id == command.candidate_id)
        candidate = candidate_query.first()
        if not candidate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

        clean_code = command.candidate_code.strip()
        # Constraint: Candidate code uniqueness
        if clean_code.lower() != candidate.candidate_code.lower():
            conflict_code = self.db.query(models.Candidate).filter(
                func.lower(models.Candidate.candidate_code) == func.lower(clean_code),
                models.Candidate.id != command.candidate_id
            ).first()
            if conflict_code:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Candidate code '{clean_code}' is already assigned to candidate '{conflict_code.name}'"
                )

        # Constraint: Staff File Number uniqueness
        clean_file = command.file_no.strip() if command.file_no and command.file_no.strip() else None
        if clean_file:
            current_file = (candidate.file_no or '').strip()
            if clean_file.lower() != current_file.lower():
                conflict_file = self.db.query(models.Candidate).filter(
                    func.lower(models.Candidate.file_no) == func.lower(clean_file),
                    models.Candidate.id != command.candidate_id
                ).first()
                if conflict_file:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Staff File Number '{clean_file}' is already assigned to candidate '{conflict_file.name}' (#{conflict_file.candidate_code})"
                    )

        office_query = self.db.query(model.Office).filter(
            func.lower(model.Office.office_code) == func.lower(command.office_code.strip())
        ).first()
        if not office_query:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Office with code: {command.office_code} does not exist")

        update_data = {
            "candidate_code": clean_code, 
            "name": command.name.strip(),
            "office_code": command.office_code.strip(),
            "manifesto_title": command.manifesto_title,
            "manifesto": command.manifesto,
            "mcs_number": command.mcs_number,
            "conraiss": command.conraiss,
            "station": command.station,
            "file_no": clean_file,
        }
        if command.image_url is not None:
            update_data["image_url"] = command.image_url

        candidate_query.update(update_data)
        self.db.commit()
        return candidate_query.first()
