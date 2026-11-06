from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core import database, utils, oauth2
from ...domain import user as user_models
from ...schemas import token as token_schemas

router = APIRouter(tags=["Admin Login"])


class AdminLoginRequest(BaseModel):
    username: str
    password: str


# ============================================================
# ADMIN LOGIN (username + password, no OTP)
# ============================================================
@router.post("/admin/login", response_model=token_schemas.Token)
def admin_login(
    credentials: AdminLoginRequest,
    db: Session = Depends(database.get_db),
):
    """
    Admin and super-admin login using username + password.
    OTP is NOT required for admin roles.
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

    # ── 5. Issue JWT access token
    access_token = oauth2.create_access_token(
        data={"user_id": str(user.id), "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "fullname": user.full_name,
    }
