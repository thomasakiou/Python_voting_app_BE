import hashlib
import secrets
from datetime import datetime, timezone
from dataclasses import dataclass
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ....domain import vote as models, candidate as cand_models, office as off_models, user as users, voting_time as vt_models
from ....core.cache import cache


@dataclass(frozen=True)
class CastVoteCommand:
    user_id: int
    candidate_code: str
    office_code: str


class CastVoteHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: "CastVoteCommand"):
        # 1. Check if voting is currently started and active
        voting_time = self.db.query(vt_models.VotingTime).first()
        if not voting_time or not voting_time.is_active or voting_time.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voting is currently closed. Voting has not yet started or has been stopped by the administrator."
            )

        # 2. Check scheduled end time if present
        if voting_time.end_time:
            now = datetime.now(timezone.utc)
            end_time = voting_time.end_time
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            if now > end_time:
                voting_time.is_active = False
                voting_time.status = "STOPPED"
                self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Voting time has elapsed. The voting session is closed."
                )

        # 3. Check user eligibility
        user = self.db.query(users.User).filter(users.User.id == command.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been disqualified / disabled. You cannot cast a vote."
            )

        if not user.is_accredited:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have not been accredited for this election."
            )

        # 4. Check office validity & disqualification
        office = self.db.query(off_models.Office).filter(
            off_models.Office.office_code == command.office_code
        ).first()
        if not office:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Office not found.")

        if office.is_disqualified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The office/category '{office.description}' has been disqualified."
            )

        # 5. Check candidate validity & disqualification
        candidate = self.db.query(cand_models.Candidate).filter(
            cand_models.Candidate.candidate_code == command.candidate_code
        ).first()
        if not candidate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

        if candidate.is_disqualified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Candidate '{candidate.name}' has been disqualified and cannot receive votes."
            )

        if candidate.office_code != office.office_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate does not belong to this office."
            )

        # 6. Ensure user hasn’t already voted for this office
        existing_vote = self.db.query(models.Vote).filter(
            models.Vote.user_id == command.user_id,
            models.Vote.office_code == office.office_code
        ).first()
        if existing_vote:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already voted for {office.description}. Each voter can vote only once per office."
            )

        # 7. Generate cryptographic vote receipt hash (Requirement 9)
        salt = secrets.token_hex(4)
        receipt_raw = f"{user.username}:{office.office_code}:{candidate.candidate_code}:{datetime.now(timezone.utc).isoformat()}:{salt}"
        receipt_hash = "MCS-" + hashlib.sha256(receipt_raw.encode()).hexdigest()[:12].upper()

        # 8. Create vote
        new_vote = models.Vote(
            user_id=command.user_id,
            user_name=user.full_name,
            office_code=office.office_code,
            office_name=office.description,
            candidate_code=candidate.candidate_code,
            candidate_name=candidate.name,
            receipt_hash=receipt_hash,
        )
        self.db.add(new_vote)
        self.db.commit()
        self.db.refresh(new_vote)

        # Invalidate results cache for this office and general cache
        cache.delete(f"results_{office.office_code}")
        cache.delete("voter_analysis")

        return {
            "id": new_vote.id,
            "user_name": user.full_name,
            "candidate_name": candidate.name,
            "candidate_code": candidate.candidate_code,
            "candidate_image_url": candidate.image_url,
            "office_name": office.description,
            "office_code": office.office_code,
            "receipt_hash": new_vote.receipt_hash,
            "created_at": new_vote.created_at,
        }
