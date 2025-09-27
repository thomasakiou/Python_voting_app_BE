from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import office as models

@dataclass(frozen=True)
class GetOfficeByIdQuery:
    id: int

class GetOfficeByIdHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetOfficeByIdQuery):
        user = self.db.query(models.Office).filter(models.Office.id == query.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Office not found")
        return user
