from ....domain import candidate as models

class ListCandidatesQuery:
    pass

class ListCandidatesHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: ListCandidatesQuery):
        return self.db.query(models.Candidate).all()
