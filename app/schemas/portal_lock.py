from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class PortalLockItem(BaseModel):
    is_locked: bool
    message: str


class PortalLockStatusResponse(BaseModel):
    contact_update: PortalLockItem
    accreditation: PortalLockItem
    election: PortalLockItem
    updated_at: Optional[datetime] = None


class PortalLockToggleRequest(BaseModel):
    portal: Literal["contact_update", "accreditation", "election"]
    is_locked: bool
    message: Optional[str] = None
