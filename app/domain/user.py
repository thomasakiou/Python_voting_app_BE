from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.sql.expression import text
from ..core.database import Base
from sqlalchemy.orm import relationship
# from .vote import Vote


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    # email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(50), nullable=False)
    phone = Column(String(20))
    must_change_password = Column(Boolean, default=True)
    role = Column(Enum("super-admin", "admin", "voter", name="user_roles"), default="user", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


    votes = relationship("Vote", back_populates="user")
