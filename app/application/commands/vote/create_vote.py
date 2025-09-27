from uuid import UUID
from pydantic import BaseModel
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from dataclasses import dataclass
from ....domain import vote as models, candidate as cand_models, office as off_models, user as users


@dataclass(frozen=True)
class CastVoteCommand:
    user_id: int
    candidate_code: str
    office_code: str


class CastVoteHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: "CastVoteCommand"):
        # 1. Get candidate
        candidate = self.db.query(cand_models.Candidate).filter(
            cand_models.Candidate.candidate_code == command.candidate_code
        ).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # 2. Get office
        office = self.db.query(off_models.Office).filter(
            off_models.Office.office_code == command.office_code
        ).first()
        if not office:
            raise HTTPException(status_code=404, detail="Office not found")
        
        # 3. Get user
        user = self.db.query(users.User).filter(
            users.User.id == command.user_id
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")


        if candidate.office_code != office.office_code:
            raise HTTPException(status_code=400, detail="Candidate does not belong to this office")

        # 4. Ensure user hasn’t already voted for this office
        existing_vote = self.db.query(models.Vote).filter(
            models.Vote.user_id == command.user_id,
            models.Vote.office_code == office.office_code
        ).first()
        if existing_vote:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already voted for this office"
            )

        # 5. Create vote
        new_vote = models.Vote(
            user_id=command.user_id,
            user_name=user.full_name,
            office_code=office.office_code,
            office_name=office.description,
            candidate_code=candidate.candidate_code,
            candidate_name=candidate.name
        )
        self.db.add(new_vote)
        self.db.commit()
        self.db.refresh(new_vote)

        # 6. Return enriched response
        return {
            "id": new_vote.id,
            "user_name": new_vote.user.full_name,
            "candidate_name": candidate.name,
            "office_name": office.description,
            "created_at": new_vote.created_at
        }


