from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import vote as models

@dataclass(frozen=True)
class GetVoterByCodeQuery:
    username: str

class GetVoterByCodeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetVoterByCodeQuery):
        voter = self.db.query(models.Vote).filter(models.Vote.user_name.ilike(f"%{query.username}%")).all()
        if not voter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voter not found")
        return voter
