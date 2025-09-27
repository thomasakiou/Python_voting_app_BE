from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core import database, utils, oauth2, config
from ...domain import user as models
from ...schemas import logout as out
from fastapi import APIRouter, Depends, Response

router = APIRouter(tags=["Logout"])


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")  # delete JWT cookie
    return {"message": "Logged out successfully"}
