from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import user as models
from ....core import utils, config
import csv
from fastapi import HTTPException, status
from ....domain import user as models
from ....core import utils
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class CreateUserCommand:
    full_name: str
    username: str
    password: str
    phone: str
    role: str
    must_change_password: str

class CreateUserHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: CreateUserCommand):
        existing = self.db.query(models.User).filter(models.User.username.ilike("%{command.username}%")).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

        # hashed_password = utils.hash_password(config.DEFAULT_ADMIN_PASSWORD)
        hashed_password = utils.hash_password(command.password)

        new_user = models.User(username=command.username, 
                               full_name=command.full_name, 
                               password=hashed_password,
                               phone=command.phone,
                               role = command.role, 
                               must_change_password=command.must_change_password)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
    


@dataclass(frozen=True)
class ImportVotersCommand:
    voters: List[dict]  # each dict: {username, full_name, phone, role, password}



class ImportVotersHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: ImportVotersCommand):
        created_users = []
        for voter in command.voters:
            # Check for duplicates
            existing = self.db.query(models.User).filter(
                models.User.username == voter["username"]
            ).first()
            if existing:
                continue  # skip duplicates

            hashed_password = utils.hash(voter.get("password", "Vote@123"))

            role = voter.get("role", "voter")
            if role not in "voter":  # validate role
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}",
                )

            new_user = models.User(
                username=voter["username"],
                full_name=voter.get("full_name", ""),
                phone=voter.get("phone"),
                password=hashed_password,
                role=role,
                must_change_password=True,
            )
            self.db.add(new_user)
            created_users.append(new_user)

        self.db.commit()
        return created_users
