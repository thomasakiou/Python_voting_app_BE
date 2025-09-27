from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import office as models

@dataclass(frozen=True)
class DeleteOfficeCommand:
    office_id: int

class DeleteOfficeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteOfficeCommand):
        office = self.db.query(models.Office).filter(models.Office.id == command.office_id).first()
        if not office:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

        self.db.delete(office)
        self.db.commit()
        return {"msg": f"Office with id: {command.office_id} deleted successfully"}