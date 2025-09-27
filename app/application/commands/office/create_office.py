from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import user as models
from ....core import utils, config
import csv
from fastapi import HTTPException, status
from ....domain import office as models
from ....core import utils
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class CreateOfficeCommand:
    # id: int
    office_code: str
    description: str


class CreateOfficeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: CreateOfficeCommand):
        existing = self.db.query(models.Office).filter(models.Office.office_code.ilike(f"%{command.office_code}%")).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

        new_office = models.Office(
                               office_code=command.office_code, 
                               description=command.description,
                                )
        self.db.add(new_office)
        self.db.commit()
        self.db.refresh(new_office)
        return new_office
    
