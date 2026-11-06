from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql.expression import text
from ..core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, nullable=False)
    admin_id = Column(Integer, nullable=True)
    admin_username = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
