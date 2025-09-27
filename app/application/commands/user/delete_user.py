from dataclasses import dataclass
from fastapi import HTTPException, status
from ....domain import user as models

@dataclass(frozen=True)
class DeleteUserCommand:
    user_id: int

class DeleteUserHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteUserCommand):
        user = self.db.query(models.User).filter(models.User.id == command.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        self.db.delete(user)
        self.db.commit()
        return {"msg": f"User with id: {command.user_id}deleted successfully"}
