from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import user as models

@dataclass(frozen=True)
class GetUserByUsernameQuery:
    username: str

class GetUserByUsernameHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: GetUserByUsernameQuery):
        user = self.db.query(models.User).filter(models.User.username == query.username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
