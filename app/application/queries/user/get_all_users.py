from ....domain import user as models

class ListUsersQuery:
    pass

class ListUsersHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: ListUsersQuery):
        return self.db.query(models.User).all()
