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
    staff_file_no: Optional[str] = None
    staff_station: Optional[str] = None
    staff_rank: Optional[str] = None
    staff_conraiss: Optional[str] = None
    staff_active: bool = True


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
            staff_file_no=command.staff_file_no.strip() if command.staff_file_no else None,
            staff_station=command.staff_station.strip() if command.staff_station else None,
            staff_rank=command.staff_rank.strip() if command.staff_rank else None,
            staff_conraiss=command.staff_conraiss.strip() if command.staff_conraiss else None,
            staff_active=command.staff_active if command.staff_active is not None else True,
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
            full_name = str(voter.get("full_name", "")).strip()
            if not username:
                continue

            existing_username = (
                self.db.query(models.User)
                .filter(models.User.username == username)
                .first()
            )
            if existing_username:
                skipped.append({
                    "username": username,
                    "full_name": full_name,
                    "reason": "Username already exists in the system"
                })
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
                        "full_name": full_name,
                        "reason": f"Email '{email}' already belongs to another user"
                    })
                    continue

            phone = voter.get("phone")
            phone = phone.strip() if phone else None

            default_pw = voter.get("password") or config.DEFAULT_VOTER_PASSWORD
            if default_pw and default_pw.startswith(("$2b$", "$2a$", "$2y$")):
                hashed_password = default_pw
            else:
                hashed_password = utils.hash_password(default_pw)
            role = voter.get("role", "voter").strip()

            staff_file_no = str(voter.get("staff_file_no") or voter.get("file_no") or voter.get("Staff_file_no") or "").strip() or None
            staff_station = str(voter.get("staff_station") or voter.get("station") or voter.get("Staff_station") or "").strip() or None
            staff_rank = str(voter.get("staff_rank") or voter.get("rank") or voter.get("Staff_rank") or "").strip() or None
            staff_conraiss = str(voter.get("staff_conraiss") or voter.get("conraiss") or voter.get("CONRAISS") or voter.get("Staff_conraiss") or "").strip() or None

            raw_active = str(voter.get("staff_active") if voter.get("staff_active") is not None else (voter.get("active") if voter.get("active") is not None else voter.get("Staff_active", ""))).strip().lower()
            if raw_active in ("no", "false", "0", "inactive", "n"):
                staff_active = False
            else:
                staff_active = True

            new_user = models.User(
                username=username,
                full_name=full_name,
                phone=phone,
                email=email,
                password=hashed_password,
                role=role,
                is_active=True,
                is_accredited=False,
                must_change_password=True,
                staff_file_no=staff_file_no,
                staff_station=staff_station,
                staff_rank=staff_rank,
                staff_conraiss=staff_conraiss,
                staff_active=staff_active,
            )
            self.db.add(new_user)
            try:
                self.db.commit()
                self.db.refresh(new_user)
                created_users.append(new_user)
            except Exception as e:
                self.db.rollback()
                skipped.append({
                    "username": username,
                    "full_name": full_name,
                    "reason": f"Database error: {str(e)}"
                })
                continue

        return {"created": created_users, "skipped": skipped}
