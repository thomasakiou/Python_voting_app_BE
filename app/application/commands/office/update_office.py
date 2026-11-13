from dataclasses import dataclass
from typing import Optional
from fastapi import HTTPException, status
from ....domain import office as models

@dataclass(frozen=True)
class UpdateOfficeCommand:
    office_id: int
    office_code: str
    description: str
    max_votes: Optional[int] = None

class UpdateOfficeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: UpdateOfficeCommand):
        office_query = self.db.query(models.Office).filter(models.Office.id == command.office_id)
        office = office_query.first()
        if not office:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Office not found")

        office.office_code = command.office_code
        office.description = command.description
        if command.max_votes is not None:
            office.max_votes = max(1, command.max_votes)

        self.db.commit()
        self.db.refresh(office)
        return office
