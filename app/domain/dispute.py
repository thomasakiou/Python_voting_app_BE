from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql.expression import text
from ..core.database import Base


class VoterDispute(Base):
    __tablename__ = "voter_disputes"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(50), nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    current_email = Column(String(255), nullable=True)
    current_phone = Column(String(50), nullable=True)
    requested_email = Column(String(255), nullable=True)
    requested_phone = Column(String(50), nullable=True)
    dispute_type = Column(String(50), default="CONTACT_UPDATE", nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, RESOLVED, REJECTED
    admin_notes = Column(Text, nullable=True)
    resolved_by = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
