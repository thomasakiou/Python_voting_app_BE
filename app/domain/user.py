from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.sql.expression import text
from ..core.database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String(255), nullable=True)
    password = Column(String, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_accredited = Column(Boolean, default=False, nullable=False)
    accredited_at = Column(TIMESTAMP(timezone=True), nullable=True)
    accredited_device_id = Column(String(255), nullable=True)
    device_info = Column(String(255), nullable=True)
    current_session_id = Column(String(255), nullable=True)
    last_active_at = Column(TIMESTAMP(timezone=True), nullable=True)
    must_change_password = Column(Boolean, default=True)
    role = Column(Enum("super-admin", "admin", "voter", name="user_roles"), default="voter", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Staff Information Fields
    staff_file_no = Column(String(100), nullable=True)
    staff_station = Column(String(150), nullable=True)
    staff_rank = Column(String(150), nullable=True)
    staff_conraiss = Column(String(50), nullable=True)
    staff_active = Column(Boolean, default=True, nullable=False, server_default=text('true'))

    votes = relationship("Vote", back_populates="user")
