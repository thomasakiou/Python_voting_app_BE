from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import candidate as models
from ....core.utils import delete_candidate_image_file

@dataclass(frozen=True)
class DeleteCandidateCommand:
    candidate_id: int

class DeleteCandidateHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteCandidateCommand):
        candidate = self.db.query(models.Candidate).filter(models.Candidate.id == command.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

        # Delete candidate image file from storage if it exists
        if candidate.image_url:
            delete_candidate_image_file(candidate.image_url)

        self.db.delete(candidate)
        self.db.commit()
        return {"msg": f"Candidate with id: {command.candidate_id} deleted successfully"}