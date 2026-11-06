from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, String, TIMESTAMP
from sqlalchemy.sql.expression import text
from ..core.database import Base


class VotingTime(Base):
    __tablename__ = "voting_times"

    id = Column(Integer, primary_key=True, nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), nullable=True)
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="NOT_STARTED", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))
