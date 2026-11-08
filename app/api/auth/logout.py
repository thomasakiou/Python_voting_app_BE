from fastapi import APIRouter, Depends, Response
from typing import Optional
from sqlalchemy.orm import Session
from jose import jwt
from ...core import database, oauth2
from ...domain import user as models

router = APIRouter(tags=["Logout"])


@router.post("/logout")
def logout(
    response: Response,
    token: Optional[str] = Depends(oauth2.oauth2_scheme),
    db: Session = Depends(database.get_db),
):
    response.delete_cookie("access_token")  # delete JWT cookie
    if token:
        try:
            payload = jwt.decode(token, oauth2.SECRET_KEY, algorithms=[oauth2.ALGORITHM])
            user_id = payload.get("user_id")
            if user_id:
                user = db.query(models.User).filter(models.User.id == user_id).first()
                if user and user.role in ("admin", "super-admin"):
                    user.current_session_id = None
                    user.device_info = None
                    user.last_active_at = None
                    db.commit()
        except Exception:
            pass
    return {"message": "Logged out successfully"}
