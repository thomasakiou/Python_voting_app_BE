from dataclasses import dataclass
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

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
        clean_username = command.username.strip()
        # 1. Constraint: No duplicate MCS Number (Username)
        existing = (
            self.db.query(models.User)
            .filter(func.lower(models.User.username) == func.lower(clean_username))
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"MCS Number (Username) '{clean_username}' already exists in the system (assigned to '{existing.full_name}')",
            )

        # 2. Constraint: No duplicate Staff File Number
        clean_file_no = command.staff_file_no.strip() if command.staff_file_no and command.staff_file_no.strip() else None
        if clean_file_no:
            existing_file = (
                self.db.query(models.User)
                .filter(func.lower(models.User.staff_file_no) == func.lower(clean_file_no))
                .first()
            )
            if existing_file:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Staff File Number '{clean_file_no}' is already assigned to user '{existing_file.username}' ({existing_file.full_name})",
                )

        # 3. Constraint: No duplicate Email if provided
        clean_email = command.email.strip().lower() if command.email and command.email.strip() else None
        if clean_email:
            existing_email = (
                self.db.query(models.User)
                .filter(func.lower(models.User.email) == func.lower(clean_email))
                .first()
            )
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{clean_email}' already belongs to user '{existing_email.username}' ({existing_email.full_name})",
                )

        hashed_password = utils.hash_password(command.password)

        new_user = models.User(
            username=clean_username,
            full_name=command.full_name.strip(),
            password=hashed_password,
            phone=command.phone.strip() if command.phone and command.phone.strip() else None,
            email=clean_email,
            role=command.role,
            is_active=True,
            is_accredited=False,
            must_change_password=command.must_change_password,
            staff_file_no=clean_file_no,
            staff_station=command.staff_station.strip() if command.staff_station and command.staff_station.strip() else None,
            staff_rank=command.staff_rank.strip() if command.staff_rank and command.staff_rank.strip() else None,
            staff_conraiss=command.staff_conraiss.strip() if command.staff_conraiss and command.staff_conraiss.strip() else None,
            staff_active=command.staff_active if command.staff_active is not None else True,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user


@dataclass(frozen=True)
class ImportVotersCommand:
    voters: List[dict]  # each dict: {username, full_name, phone, email, role, password, staff_file_no...}


class ImportVotersHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: ImportVotersCommand):
        created_users = []
        skipped = []
        seen_usernames = set()
        seen_file_nos = set()

        for voter in command.voters:
            username = str(voter.get("username", "")).strip()
            full_name = str(voter.get("full_name", "")).strip()
            if not username:
                continue

            username_lower = username.lower()

            # 1. Constraint: Check intra-file duplicate MCS Number (Username)
            if username_lower in seen_usernames:
                skipped.append({
                    "username": username,
                    "full_name": full_name,
                    "reason": f"Duplicate MCS Number (Username) '{username}' within uploaded CSV file"
                })
                continue

            # 2. Constraint: Check database duplicate MCS Number (Username)
            existing_username = (
                self.db.query(models.User)
                .filter(func.lower(models.User.username) == username_lower)
                .first()
            )
            if existing_username:
                skipped.append({
                    "username": username,
                    "full_name": full_name,
                    "reason": f"MCS Number (Username) '{username}' already exists in the system ({existing_username.full_name})"
                })
                continue

            # 3. Constraint: Check Staff File Number (intra-file and in database)
            staff_file_no = str(voter.get("staff_file_no") or voter.get("file_no") or voter.get("Staff_file_no") or "").strip() or None
            if staff_file_no:
                file_no_lower = staff_file_no.lower()
                if file_no_lower in seen_file_nos:
                    skipped.append({
                        "username": username,
                        "full_name": full_name,
                        "reason": f"Duplicate Staff File Number '{staff_file_no}' within uploaded CSV file"
                    })
                    continue

                existing_file_no = (
                    self.db.query(models.User)
                    .filter(func.lower(models.User.staff_file_no) == file_no_lower)
                    .first()
                )
                if existing_file_no:
                    skipped.append({
                        "username": username,
                        "full_name": full_name,
                        "reason": f"Staff File Number '{staff_file_no}' is already assigned to user '{existing_file_no.username}' ({existing_file_no.full_name})"
                    })
                    continue

            # 4. Check duplicate email if present
            email = voter.get("email")
            email = str(email).strip().lower() if email and str(email).strip() else None
            if email:
                existing_email = (
                    self.db.query(models.User)
                    .filter(func.lower(models.User.email) == email)
                    .first()
                )
                if existing_email:
                    skipped.append({
                        "username": username,
                        "full_name": full_name,
                        "reason": f"Email '{email}' already belongs to user '{existing_email.username}' ({existing_email.full_name})"
                    })
                    continue

            # Mark as processed in this batch to prevent intra-file duplicates
            seen_usernames.add(username_lower)
            if staff_file_no:
                seen_file_nos.add(staff_file_no.lower())

            phone = voter.get("phone")
            phone = str(phone).strip() if phone and str(phone).strip() else None

            default_pw = voter.get("password") or config.DEFAULT_VOTER_PASSWORD
            if default_pw and default_pw.startswith(("$2b$", "$2a$", "$2y$")):
                hashed_password = default_pw
            else:
                hashed_password = utils.hash_password(default_pw)
            role = str(voter.get("role", "voter")).strip()

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
                seen_usernames.discard(username_lower)
                if staff_file_no:
                    seen_file_nos.discard(staff_file_no.lower())
                continue

        return {"created": created_users, "skipped": skipped}
