from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import office as models

@dataclass(frozen=True)
class UpdateOfficeCommand:
    office_id: int
    office_code: str
    description: str

class UpdateOfficeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: UpdateOfficeCommand):
        office_query = self.db.query(models.Office).filter(models.Office.id == command.office_id)
        office = office_query.first()
        if not office:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Office not found")

        # email_exists = self.db.query(models.Office).filter(models.Office.email == command.email).first()
        # if email_exists and email_exists.id != command.user_id:
        #     raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already taken")

        # office_query.update({"office_code": command.office_code, 
        #                      "description": command.description})

        office.office_code = command.office_code
        office.description = command.description

        self.db.commit()
        self.db.refresh(office)
        return office_query.first()
