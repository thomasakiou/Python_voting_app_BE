import hashlib
import secrets
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ....domain import vote as models, candidate as cand_models, office as off_models, user as users, voting_time as vt_models
from ....core.cache import cache


@dataclass(frozen=True)
class CastVoteCommand:
    user_id: int
    office_code: str
    candidate_code: Optional[str] = None
    candidate_codes: Optional[List[str]] = None


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

        # 5. Extract chosen candidates list
        chosen_codes: List[str] = []
        if command.candidate_codes:
            chosen_codes = [c.strip() for c in command.candidate_codes if c and str(c).strip()]
        elif command.candidate_code:
            chosen_codes = [command.candidate_code.strip()]

        if not chosen_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No candidate selected. Please select at least one candidate."
            )

        # 6. Ensure voter cannot vote for the same candidate twice
        if len(chosen_codes) != len(set(chosen_codes)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot vote for the same candidate more than once."
            )

        # 7. Check max allowed selections for this office
        max_allowed = getattr(office, "max_votes", 1) or 1
        if len(chosen_codes) > max_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can select a maximum of {max_allowed} candidate(s) for {office.description}. You selected {len(chosen_codes)}."
            )

        # 8. Ensure user hasn’t already voted for this office
        existing_vote = self.db.query(models.Vote).filter(
            models.Vote.user_id == command.user_id,
            models.Vote.office_code == office.office_code
        ).first()
        if existing_vote:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already voted for {office.description}. Each voter can vote only once per office contest."
            )

        # 9. Check each candidate's validity & disqualification
        validated_candidates = []
        for cand_code in chosen_codes:
            candidate = self.db.query(cand_models.Candidate).filter(
                cand_models.Candidate.candidate_code == cand_code
            ).first()
            if not candidate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Candidate '{cand_code}' not found."
                )

            if candidate.is_disqualified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Candidate '{candidate.name}' has been disqualified and cannot receive votes."
                )

            if candidate.office_code != office.office_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Candidate '{candidate.name}' does not belong to {office.description}."
                )
            validated_candidates.append(candidate)

        # 10. Generate cryptographic vote receipt hashes & create vote records
        created_votes = []
        receipt_hashes = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for cand in validated_candidates:
            salt = secrets.token_hex(4)
            receipt_raw = f"{user.username}:{office.office_code}:{cand.candidate_code}:{now_iso}:{salt}"
            receipt_hash = "MCS-" + hashlib.sha256(receipt_raw.encode()).hexdigest()[:12].upper()
            receipt_hashes.append(receipt_hash)

            new_vote = models.Vote(
                user_id=command.user_id,
                user_name=user.username,
                office_code=office.office_code,
                office_name=office.description,
                candidate_code=cand.candidate_code,
                candidate_name=cand.name,
                receipt_hash=receipt_hash,
            )
            self.db.add(new_vote)
            created_votes.append(new_vote)

        self.db.commit()
        for v in created_votes:
            self.db.refresh(v)

        # Invalidate results cache for this office and general cache
        cache.delete(f"results_{office.office_code}")
        cache.delete("voter_analysis")

        primary_vote = created_votes[0]
        combined_candidate_names = ", ".join([c.name for c in validated_candidates])
        combined_candidate_codes = ", ".join([c.candidate_code for c in validated_candidates])
        combined_receipt_hashes = ", ".join(receipt_hashes)
        first_img = validated_candidates[0].image_url if len(validated_candidates) == 1 else None

        return {
            "id": primary_vote.id,
            "username": user.username,
            "user_name": user.username,
            "full_name": user.full_name,
            "candidate_name": combined_candidate_names,
            "candidate_code": combined_candidate_codes,
            "candidate_image_url": first_img,
            "candidate_codes": [c.candidate_code for c in validated_candidates],
            "receipt_hashes": receipt_hashes,
            "office_name": office.description,
            "office_code": office.office_code,
            "receipt_hash": combined_receipt_hashes,
            "created_at": primary_vote.created_at,
        }
