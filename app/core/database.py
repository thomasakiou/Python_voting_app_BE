from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings


# # Escape special characters in password
# from urllib.parse import quote_plus
# safe_password = quote_plus(settings.database_password)

SQLALCHEMY_DATABASE_URL = settings.db_url
# f'postgresql://{settings.database_username}:{safe_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}'


engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()