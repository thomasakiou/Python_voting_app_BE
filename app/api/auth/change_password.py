from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core import database, utils, oauth2, config
from ...core.config import settings
from ...domain import user as models
from ...schemas import user as schemas, change_password as change_password_schemas


router = APIRouter(prefix="/api", tags=["Change Password"])


# ===============================
# CHANGE PASSWORD   
# ===============================
@router.post("/change-password")
def change_password(request: change_password_schemas.ChangePasswordRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # user.password = utils.hash_password(user.password)

    if not utils.verify_password(request.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Old password is incorrect")

    user.password = utils.hash_password(request.new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)

    return {"message": "Password changed successfully. You can now log in with your new password."}
