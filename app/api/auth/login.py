from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core import database, utils, oauth2, config
from ...domain import user as models
from ...schemas import user as schemas, token as token_schemas, change_password as change_password_schemas, login

router = APIRouter(tags=["Login"])

# ===============================
# LOGIN
# ===============================
@router.post("/login", response_model=token_schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # Authenticate the user
    user = db.query(models.User).filter(models.User.username == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid credentials")
    
    if not utils.verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid credentials")
    
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must change your password before logging in."
    )
    
    #create token
    access_token = oauth2.create_access_token(data={"user_id": str(user.id), "role": user.role})
    #return token
    return {"access_token": access_token, "token_type": "bearer"}



