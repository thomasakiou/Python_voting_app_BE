from sqlalchemy.orm import Session
from ....domain import user as models
from fastapi import HTTPException, status
from dataclasses import dataclass
from typing import Any


# ////////////////////////////DISABLE VOTERS
@dataclass(frozen=True)
class DisableAllVotersCommand:
    def __init__(self):
        pass  # no additional input needed


class DisableAllVotersHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DisableAllVotersCommand) -> dict[str, Any]:
        voters = self.db.query(models.User).filter(
            models.User.role == "voter",
            models.User.is_active == True
        ).all()

        if not voters:
            return {"message": "No active voters found."}

        for voter in voters:
            voter.is_active = False

        self.db.commit()
        return {"message": f"{len(voters)} voters have been disabled successfully."}




# ////////////////////ENABLE VOTERS
# application/commands/user/enable_voters.py
@dataclass(frozen=True)
class EnableAllVotersCommand:
    def __init__(self):
        pass  # no additional input needed


class EnableAllVotersHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: EnableAllVotersCommand) -> dict[str, Any]:
        voters = self.db.query(models.User).filter(
            models.User.role == "voter",
            models.User.is_active == False
        ).all()

        if not voters:
            return {"message": "No inactive voters found."}

        for voter in voters:
            voter.is_active = True

        self.db.commit()
        return {"message": f"{len(voters)} voters have been re-enabled successfully."}
