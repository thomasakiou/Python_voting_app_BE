import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from ...core import database, utils, oauth2
from ...core.config import settings
from ...domain import user as user_models
from ...schemas import token as token_schemas

router = APIRouter(tags=["Admin Login"])


class AdminLoginRequest(BaseModel):
    username: str
    password: str
    device_id: Optional[str] = None
    force: Optional[bool] = False


# ============================================================
# CHECK ADMIN ACTIVE SESSION STATUS (Public for login page)
# ============================================================
@router.get("/admin/session-status")
def get_admin_session_status(db: Session = Depends(database.get_db)):
    """
    Checks if a regular administrator session is currently active.
    Super-admin is exempt and can log in at anytime.
    """
    admin_user = (
        db.query(user_models.User)
        .filter(user_models.User.role == "admin")
        .filter(user_models.User.current_session_id.isnot(None))
        .first()
    )
    if not admin_user:
        return {"has_active_session": False}

    # Check if the active session has been abandoned longer than the session timeout
    timeout_seconds = getattr(settings, "admin_session_timeout_minutes", 15) * 60
    if admin_user.last_active_at is not None:
        now = datetime.now(timezone.utc)
        last_active = admin_user.last_active_at
        if last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=timezone.utc)
        if (now - last_active).total_seconds() > timeout_seconds:
            # Session expired due to prolonged inactivity
            admin_user.current_session_id = None
            admin_user.device_info = None
            admin_user.last_active_at = None
            db.commit()
            return {"has_active_session": False}

    return {
        "has_active_session": True,
        "message": "An administrator session is currently active. (Super-admin may log in at anytime).",
    }


# ============================================================
# ADMIN LOGIN (username + password, no OTP, Single Session)
# ============================================================
@router.post("/admin/login", response_model=token_schemas.Token)
def admin_login(
    credentials: AdminLoginRequest,
    db: Session = Depends(database.get_db),
):
    """
    Admin and super-admin login using username + password.
    - Super-admin: Can log in at ANYTIME without session or count restrictions.
    - Admin (created by super-admin): Can ONLY log in ONCE (single-use admin account).
      Once used, they cannot log in again unless the super-admin creates another account.
    """
    # ── 1. Look up the user by username (case-insensitive)
    cleaned_username = credentials.username.strip()
    user = (
        db.query(user_models.User)
        .filter(func.lower(user_models.User.username) == func.lower(cleaned_username))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials",
        )

    # ── 2. Only allow admin and super-admin through this endpoint
    if user.role not in ("admin", "super-admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This login endpoint is for administrators only.",
        )

    # ── 3. Verify password
    if not utils.verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials",
        )

    # ── 4. Check the account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is deactivated. Please contact the super-administrator.",
        )

    now = datetime.now(timezone.utc)

    # ── 5. SINGLE ACTIVE SESSION RULE FOR ADMIN ACCOUNTS
    # When an admin account is currently logged in, that SAME account cannot be logged into again.
    # When the admin logs out (or super-admin terminates session), the account is released to log in again.
    # Super-admin is exempt and can log in at anytime.
    if user.role == "admin" and user.current_session_id and not credentials.force:
        timeout_seconds = getattr(settings, "admin_session_timeout_minutes", 15) * 60
        is_active = True
        if user.last_active_at is not None:
            last_active = user.last_active_at
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            if (now - last_active).total_seconds() > timeout_seconds:
                # Inactive session has timed out -> release the account automatically
                user.current_session_id = None
                user.device_info = None
                user.last_active_at = None
                user.admin_login_count = 0
                db.commit()
                is_active = False

        if is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This admin account is currently logged in on another session. "
                    "You cannot log in until that session logs out or is released by the super administrator."
                ),
            )

    # ── 6. Issue new session ID and bind active session
    session_id = str(uuid.uuid4())
    user.current_session_id = session_id
    if credentials.device_id:
        user.device_info = credentials.device_id.strip()
    user.last_active_at = now
    user.admin_login_count = 1

    db.commit()

    # ── 8. Issue JWT access token
    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id), "role": user.role, "session_id": session_id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "fullname": user.full_name or user.username,
        "role": user.role,
        "username": user.username,
    }


class AgentLoginRequest(BaseModel):
    username: str
    password: str


# ============================================================
# AGENT LOGIN (username + password alone, No OTP, No device lock)
# ============================================================
@router.post("/agents/login", response_model=token_schemas.Token)
@router.post("/agents/login/", response_model=token_schemas.Token)
@router.post("/agent/login", response_model=token_schemas.Token)
@router.post("/agent/login/", response_model=token_schemas.Token)
def agent_login(
    credentials: AgentLoginRequest,
    db: Session = Depends(database.get_db),
):
    """
    Agent login using username + password alone.
    No OTP, no device binding required.
    Agents and administrators can log in here to view the live election monitor.
    """
    cleaned_username = credentials.username.strip()
    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == cleaned_username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid username or password",
        )

    if user.role not in ("agent", "admin", "super-admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: This portal is for accredited election agents and administrators.",
        )

    if not utils.verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your agent account is deactivated. Please contact the administrator.",
        )

    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id), "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "fullname": user.full_name or user.username,
        "role": user.role,
        "username": user.username,
    }

