from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, TIMESTAMP
from sqlalchemy.sql.expression import text
from ..core.database import Base


class VotingTime(Base):
    __tablename__ = "voting_times"

    id = Column(Integer, primary_key=True, nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))
