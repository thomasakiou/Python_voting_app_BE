from dataclasses import dataclass
# from fastapi import HTTPException, status
# from ....domain import user as models
from ....core import utils, config
# import csv
from fastapi import HTTPException, status
from ....domain import user as models
# from ....core import utils
# from dataclasses import dataclass
# from typing import List


# ================================
# TOGGLE USER FIELD (is_active)
# ================================
@dataclass(frozen=True)
class ToggleUserStatusCommand:
    user_id: int
    is_active: bool
    # updated_by: int


class ToggleUserStatusHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: ToggleUserStatusCommand):
        user = self.db.query(models.User).filter(models.User.id == command.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_active = command.is_active
        # user.updated_by = command.updated_by

        self.db.commit()
        self.db.refresh(user)
        return user