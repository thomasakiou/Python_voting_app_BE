from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import candidate as models

@dataclass(frozen=True)
class DeleteCandidateCommand:
    candidate_id: int

class DeleteCandidateHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteCandidateCommand):
        user = self.db.query(models.Candidate).filter(models.Candidate.id == command.candidate_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        self.db.delete(user)
        self.db.commit()
        return {"msg": f"Candidate with id: {command.candidate_id} deleted successfully"}