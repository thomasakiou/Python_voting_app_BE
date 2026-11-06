from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import voting_time as models
from datetime import datetime


@dataclass(frozen=True)
class GetVotingTimeQuery:
    pass


class GetVotingTimeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetVotingTimeQuery):
        # Get the voting time record (should only be one)
        voting_time = self.db.query(models.VotingTime).first()
        
        if not voting_time:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voting time not configured"
            )
        
        return voting_time
