# from dataclasses import dataclass
# from fastapi import HTTPException, status
# from ....domain import user as models

# @dataclass(frozen=True)
# class UpdateUserCommand:
#     user_id: int
#     full_name: str
#     email: str

# class UpdateUserHandler:
#     def __init__(self, db):
#         self.db = db

#     def handle(self, command: UpdateUserCommand):
#         user_query = self.db.query(models.User).filter(models.User.id == command.user_id)
#         user = user_query.first()

#         if not user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

#         email_exists = self.db.query(models.User).filter(models.User.email == command.email).first()
#         if email_exists and email_exists.id != command.user_id:
#             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already taken")

#         user_query.update({"full_name": command.full_name, "email": command.email})
#         self.db.commit()
#         return user_query.first()
