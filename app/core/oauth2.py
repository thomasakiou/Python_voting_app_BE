from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..schemas import user as schemas, token as tokenData
from ..domain import user as models
from .database import get_db
from sqlalchemy.orm import Session
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        role = to_encode.get("role")
        if role in ("admin", "super-admin"):
            # 24 hours (1440 minutes) for admins to monitor the election without session expiration
            admin_minutes = getattr(settings, "admin_token_expire_minutes", 1440)
            expire = datetime.utcnow() + timedelta(minutes=admin_minutes)
        else:
            # 2 hours for voters
            voter_minutes = max(getattr(settings, "access_token_expire_minutes", 120), 120)
            expire = datetime.utcnow() + timedelta(minutes=voter_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        role: str = payload.get("role")
        session_id: str = payload.get("session_id")

        if id is None:
            raise credentials_exception
        token_data = tokenData.TokenData(id=id, role=role, session_id=session_id)
    except JWTError:
        raise credentials_exception
    
    return token_data


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    if not user:
        raise credentials_exception

    # Enforce single session for admin accounts
    if user.role in ("admin", "super-admin") and user.current_session_id:
        if token_data.session_id != user.current_session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin session expired: A new login was initiated on another device.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Keep active admin session alive and update activity timestamp (throttled to every 30s)
        now = datetime.now(timezone.utc)
        should_update = False
        if user.last_active_at is None:
            should_update = True
        else:
            last_active = user.last_active_at
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
            if (now - last_active).total_seconds() > 30:
                should_update = True
        if should_update:
            user.last_active_at = now
            try:
                db.commit()
            except Exception:
                db.rollback()

    return user


def role_required(allowed_roles: list[str]):
    def wrapper(current_user: models.User = Depends(get_current_user)):
        if current_user is None:
            raise HTTPException(
                status_code=403,
                detail="Access forbidden: no user found"
            )
        if current_user.role not in allowed_roles: 
            raise HTTPException(
                status_code=403,
                detail=f"Access forbidden for role: {current_user.role}"
            )
        return current_user
    return wrapper
