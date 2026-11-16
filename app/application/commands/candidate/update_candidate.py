from dataclasses import dataclass
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from ....domain import candidate as models, office as model
from ....core.utils import delete_candidate_image_file

@dataclass(frozen=True)
class UpdateCandidateCommand:
    candidate_id: int
    candidate_code: str
    name: str
    office_code: str
    image_url: Optional[str] = None
    image_url_set: bool = False
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

        # Handle candidate image updating / removal
        if command.image_url_set or command.image_url is not None:
            if command.image_url:
                clean_img = command.image_url.strip()
                if clean_img:
                    if candidate.image_url and candidate.image_url != clean_img:
                        delete_candidate_image_file(candidate.image_url)
                    update_data["image_url"] = clean_img
                else:
                    # User passed empty string "" -> completely remove image and delete file
                    if candidate.image_url:
                        delete_candidate_image_file(candidate.image_url)
                    update_data["image_url"] = None
            else:
                # User passed None/null -> completely remove image and delete file
                if candidate.image_url:
                    delete_candidate_image_file(candidate.image_url)
                update_data["image_url"] = None

        candidate_query.update(update_data)
        self.db.commit()
        return candidate_query.first()
