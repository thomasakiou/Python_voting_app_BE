from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import candidate as models, office as model

@dataclass(frozen=True)
class UpdateCandidateCommand:
    candidate_id: int
    candidate_code: str
    name: str
    office_code: str

class UpdateCandidateHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: UpdateCandidateCommand):
        candidate_query = self.db.query(models.Candidate).filter(models.Candidate.id == command.candidate_id)
        candidate = candidate_query.first()
        if not candidate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        office_query = self.db.query(model.Office).filter(model.Office.office_code.ilike("%{command.office_code}%")).first()
        if not office_query:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Office with code: {command.office_code} does not exist")

        candidate_query.update({"candidate_code": command.candidate_code, 
                                "name": command.name,
                                "office_code": command.office_code})
        self.db.commit()
        return candidate_query.first()
