from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.sql.expression import text
from ..core.database import Base
from sqlalchemy.orm import relationship


class Office(Base):
    __tablename__ = "offices"

    id = Column(Integer, primary_key=True, nullable=False)
    office_code = Column(String(6), unique=True, nullable=False)
    description = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


    candidates = relationship("Candidate", back_populates="office")
    votes = relationship("Vote", back_populates="office")
