from sqlalchemy import Column, Integer, Boolean, String, TIMESTAMP
from sqlalchemy.sql.expression import text
from ..core.database import Base


class PortalLock(Base):
    __tablename__ = "portal_locks"

    id = Column(Integer, primary_key=True, default=1)
    is_contact_update_locked = Column(Boolean, default=False, nullable=False)
    is_accreditation_locked = Column(Boolean, default=False, nullable=False)
    is_election_locked = Column(Boolean, default=False, nullable=False)
    contact_update_message = Column(
        String(500),
        default="The Voter Contact Update portal is currently closed by the election administrator.",
        nullable=True,
    )
    accreditation_message = Column(
        String(500),
        default="Voter Accreditation is currently closed by the election administrator.",
        nullable=True,
    )
    election_message = Column(
        String(500),
        default="The Election portal is currently closed by the election administrator.",
        nullable=True,
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )
