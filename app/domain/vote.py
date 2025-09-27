from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, TIMESTAMP, Enum, UniqueConstraint
from sqlalchemy.sql.expression import text
from ..core.database import Base
from sqlalchemy.orm import relationship


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_name = Column(String, nullable=False) 
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    office_code = Column(String, ForeignKey("offices.office_code", ondelete="CASCADE"))
    office_name = Column(String, nullable=False)
    candidate_code = Column(String, ForeignKey("candidates.candidate_code", ondelete="CASCADE"))
    candidate_name = Column(String, nullable=False)

    user = relationship("User", back_populates="votes")
    office = relationship("Office", back_populates="votes")
    candidate = relationship("Candidate", back_populates="votes")

    # Prevent a user from voting more than once for the same office
    __table_args__ = (
        UniqueConstraint("user_id", "office_code", name="unique_vote_per_office"),
    )
