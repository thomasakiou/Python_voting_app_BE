from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import vote as models


@dataclass(frozen=True)
class GetVoterByIdQuery:
    userId: int


class GetVoterByIdHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetVoterByIdQuery):
        userId = self.db.query(models.Vote).filter(models.Vote.user_id == query.userId).all()
        if not userId:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voter not found")
        return userId