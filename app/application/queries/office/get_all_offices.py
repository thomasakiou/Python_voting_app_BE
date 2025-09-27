from ....domain import office as models

class ListOfficesQuery:
    pass

class ListOfficesHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: ListOfficesQuery):
        return self.db.query(models.Office).all()
