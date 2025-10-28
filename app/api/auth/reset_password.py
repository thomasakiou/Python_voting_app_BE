from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core import database, utils, oauth2, config
from ...core.config import settings
from ...domain import user as models
from ...schemas import user as schemas, change_password as change_password_schemas

router = APIRouter(tags=["Reset Password"])

# ===============================
# RESET PASSWORD
# ===============================
@router.post("/reset-password/{username}")
def reset_password(username: str, db: Session = Depends(database.get_db), 
                   current_user=Depends(oauth2.role_required(["super-admin", "admin"]))):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password = utils.hash_password(config.DEFAULT_VOTER_PASSWORD)
    user.must_change_password = True  # 🔹 force change again
    db.commit()
    db.refresh(user)

    return {"message": f"Password for {username} has been reset to default. User must change it on next login."}