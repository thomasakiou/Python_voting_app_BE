from dataclasses import dataclass
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ....domain import user as models
from ....core import utils, config


@dataclass(frozen=True)
class CreateUserCommand:
    full_name: str
    username: str
    password: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = "voter"
    must_change_password: bool = True


class CreateUserHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateUserCommand):
        existing = (
            self.db.query(models.User)
            .filter(models.User.username == command.username.strip())
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{command.username}' already exists",
            )

        hashed_password = utils.hash_password(command.password)

        new_user = models.User(
            username=command.username.strip(),
            full_name=command.full_name.strip(),
            password=hashed_password,
            phone=command.phone.strip() if command.phone else None,
            email=command.email.strip().lower() if command.email else None,
            role=command.role,
            is_active=True,
            is_accredited=False,
            must_change_password=command.must_change_password,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user


@dataclass(frozen=True)
class ImportVotersCommand:
    voters: List[dict]  # each dict: {username, full_name, phone, email, role, password}


class ImportVotersHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: ImportVotersCommand):
        created_users = []
        skipped = []

        for voter in command.voters:
            username = str(voter["username"]).strip()
            if not username:
                continue

            existing_username = (
                self.db.query(models.User)
                .filter(models.User.username == username)
                .first()
            )
            if existing_username:
                skipped.append({"username": username, "reason": "Username already exists"})
                continue

            email = voter.get("email")
            email = email.strip().lower() if email else None
            if email:
                existing_email = (
                    self.db.query(models.User)
                    .filter(models.User.email == email)
                    .first()
                )
                if existing_email:
                    skipped.append({
                        "username": username,
                        "reason": f"Email '{email}' already belongs to another user"
                    })
                    continue

            phone = voter.get("phone")
            phone = phone.strip() if phone else None

            default_pw = voter.get("password") or config.DEFAULT_VOTER_PASSWORD
            hashed_password = utils.hash_password(default_pw)
            role = voter.get("role", "voter").strip()

            new_user = models.User(
                username=username,
                full_name=voter.get("full_name", "").strip(),
                phone=phone,
                email=email,
                password=hashed_password,
                role=role,
                is_active=True,
                is_accredited=False,
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
