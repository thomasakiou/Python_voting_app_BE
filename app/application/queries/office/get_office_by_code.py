from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import office as models

@dataclass(frozen=True)
class GetOfficeByCodeQuery:
    office_code: str

class GetOfficeByCodeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetOfficeByCodeQuery):
        user = self.db.query(models.Office).filter(models.Office.office_code.ilike(f"%{query.office_code}%")).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Office not found")
        return user
