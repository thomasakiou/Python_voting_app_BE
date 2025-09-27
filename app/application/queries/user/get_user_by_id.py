# from dataclasses import dataclass
# from fastapi import HTTPException, status
# from ....domain import user as models

# @dataclass(frozen=True)
# class GetUserByIdQuery:
#     id: int

# class GetUserByIdHandler:
#     def __init__(self, db):
#         self.db = db

#     def handle(self, query: GetUserByIdQuery):
#         user = self.db.query(models.User).filter(models.User.id == query.id).first()
#         if not user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
#         return user
