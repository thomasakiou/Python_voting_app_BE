from ....domain import vote as models

class ListVotesQuery:
    pass

class ListVotesHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, query: ListVotesQuery):
        return self.db.query(models.Vote).all()
