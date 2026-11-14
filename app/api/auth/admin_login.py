import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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
    Checks if an administrator session is currently active.
    Used by the login page to display an alert if another session is already open.
    """
    admin_user = (
        db.query(user_models.User)
        .filter(user_models.User.role.in_(["admin", "super-admin"]))
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
        "message": "Another admin session is currently logged in. You cannot log in until that session logs out.",
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
    OTP is NOT required for admin roles.
    Enforces single-device login with priority to the first logged-in device:
    A second device is not allowed to log in while an active session exists.
    """
    # ── 1. Look up the user by username
    user = (
        db.query(user_models.User)
        .filter(user_models.User.username == credentials.username)
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

    # ── 5. Enforce single-session rule:
    # When one session is logged in, do not log in a second person unless force=True.
    # If the login is coming from the SAME device, allow re-login to recover the session.
    now = datetime.now(timezone.utc)
    if user.current_session_id and not credentials.force:
        is_same_device = bool(
            credentials.device_id
            and user.device_info
            and credentials.device_id.strip() == user.device_info.strip()
        )
        if not is_same_device:
            timeout_seconds = getattr(settings, "admin_session_timeout_minutes", 15) * 60
            is_active = True
            if user.last_active_at is not None:
                last_active = user.last_active_at
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)
                if (now - last_active).total_seconds() > timeout_seconds:
                    is_active = False

            if is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Another administrator session is currently logged in. "
                        "Only one admin session is allowed at a time. "
                        "You cannot log in until that session logs out."
                    ),
                )

    # ── 6. Issue new session ID and bind to this device
    session_id = str(uuid.uuid4())
    user.current_session_id = session_id
    if credentials.device_id:
        user.device_info = credentials.device_id.strip()
    user.last_active_at = now
    db.commit()

    # ── 7. Issue JWT access token
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

