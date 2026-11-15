from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.sql.expression import text
from ..core.database import Base
from sqlalchemy.orm import relationship


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, nullable=False)
    candidate_code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    image_url = Column(String, nullable=True)
    is_disqualified = Column(Boolean, default=False, nullable=False)
    manifesto_title = Column(String(255), nullable=True)
    manifesto = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    office_code = Column(String, ForeignKey("offices.office_code", ondelete="CASCADE"))

    # Staff Information
    mcs_number = Column(String(50), nullable=True)
    conraiss = Column(String(50), nullable=True)
    station = Column(String(150), nullable=True)
    file_no = Column(String(100), nullable=True)
    is_hidden = Column(Boolean, default=False, nullable=False, server_default=text('false'))

    office = relationship("Office", back_populates="candidates")
    votes = relationship("Vote", back_populates="candidate")

    @property
    def vote_count(self) -> int:
        try:
            return len(self.votes) if self.votes is not None else 0
        except Exception:
            return 0
