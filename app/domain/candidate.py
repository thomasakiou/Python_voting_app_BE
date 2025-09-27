from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.sql.expression import text
from ..core.database import Base
from sqlalchemy.orm import relationship


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, nullable=False)
    candidate_code = Column(String(4), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    office_code = Column(String, ForeignKey("offices.office_code", ondelete="CASCADE"))
    

    office = relationship("Office", back_populates="candidates")
    votes = relationship("Vote", back_populates="candidate")
