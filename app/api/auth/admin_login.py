import uuid
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

    # ── 5. Enforce single-device priority: do not allow second device to log in if active session exists
    now = datetime.now(timezone.utc)
    if user.current_session_id:
        is_active_session = False
        if user.last_active_at is not None:
            last_active = user.last_active_at
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            inactivity_duration = (now - last_active).total_seconds()
            timeout_seconds = getattr(settings, "admin_session_timeout_minutes", 15) * 60
            if inactivity_duration < timeout_seconds:
                is_active_session = True
        else:
            # If current_session_id is present but last_active_at was not recorded,
            # allow this login to establish the new session with last_active_at tracked.
            is_active_session = False

        if is_active_session:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "An active administrator session is already running on another device. "
                    "Only one device can be logged in at a time. "
                    "Please log out from the active device first before logging in here."
                ),
            )

    # ── 6. Issue new session ID to enforce single login instance
    session_id = str(uuid.uuid4())
    user.current_session_id = session_id
    user.last_active_at = now
    db.commit()

    # ── 7. Issue JWT access token
    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id), "role": user.role, "session_id": session_id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "fullname": user.full_name,
    }
