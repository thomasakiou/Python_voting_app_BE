from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum as PyEnum

class UserRole(str, PyEnum):
    super_admin = "super-admin"
    admin = "admin"
    voter = "voter"


# ===============================================================================================
# USER SCHEMA
# ===============================================================================================
class UserBase(BaseModel):
    username: str
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    created_at: datetime
    role: UserRole
    is_active: bool = True
    is_accredited: bool = False
    accredited_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserOut(UserBase):
    id: int
    username: str
    role: UserRole
    is_active: Optional[bool] = True
    is_accredited: Optional[bool] = False
    accredited_at: Optional[datetime] = None
    accredited_device_id: Optional[str] = None
    device_info: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class UserStatsOut(BaseModel):
    total_voters: int
    accredited_voters: int
    unaccredited_voters: int
    eligible_voters: int
    non_eligible_voters: int
    active_voters: int
    disabled_voters: int
    total_votes_cast: int
    turnout_percentage: float
