from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import voting_time as models
from datetime import datetime


@dataclass(frozen=True)
class SetVotingTimeCommand:
    start_time: datetime
    end_time: datetime


class SetVotingTimeHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: SetVotingTimeCommand):
        # Validate that end_time is after start_time
        if command.end_time <= command.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="End time must be after start time"
            )
        
        # Check if a voting time record already exists (singleton pattern)
        existing = self.db.query(models.VotingTime).first()
        
        if existing:
            # Update existing record
            existing.start_time = command.start_time
            existing.end_time = command.end_time
            existing.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new record
            new_voting_time = models.VotingTime(
                start_time=command.start_time,
                end_time=command.end_time
            )
            self.db.add(new_voting_time)
            self.db.commit()
            self.db.refresh(new_voting_time)
            return new_voting_time
