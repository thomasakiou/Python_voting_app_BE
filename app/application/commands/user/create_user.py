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
        skipped = []  # list of {username, reason}

        for voter in command.voters:
            username = voter["username"]

            # ── Check for duplicate username
            existing_username = self.db.query(models.User).filter(
                models.User.username == username
            ).first()
            if existing_username:
                skipped.append({"username": username, "reason": "Username already exists"})
                continue

            # ── Check for duplicate email (only if email provided)
            email = voter.get("email") or None
            if email:
                existing_email = self.db.query(models.User).filter(
                    models.User.email == email
                ).first()
                if existing_email:
                    skipped.append({"username": username, "reason": f"Email '{email}' already belongs to another user"})
                    continue

            hashed_password = utils.hash(voter.get("password", "Vote@123"))

            role = voter.get("role", "voter")
            if role != "voter":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role '{role}' for username '{username}'. Only 'voter' role is allowed for CSV import.",
                )

            new_user = models.User(
                username=username,
                full_name=voter.get("full_name", ""),
                phone=voter.get("phone"),
                email=email,
                password=hashed_password,
                role=role,
                must_change_password=True,
            )
            self.db.add(new_user)
            try:
                self.db.commit()
                self.db.refresh(new_user)
                created_users.append(new_user)
            except Exception as e:
                self.db.rollback()
                skipped.append({"username": username, "reason": f"Database error: {str(e)}"})
                continue

        return {"created": created_users, "skipped": skipped}
