from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


# ===============================================================================================
# VOTING TIME SCHEMA
# ===============================================================================================
class VotingTimeBase(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class VotingTimeCreate(VotingTimeBase):
    start_time: datetime
    end_time: datetime

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        if 'start_time' in info.data and info.data['start_time'] and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

    class Config:
        from_attributes = True


class VotingTimeResponse(VotingTimeBase):
    id: int
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VotingTimeOut(BaseModel):
    id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool
    status: str  # 'NOT_STARTED', 'ACTIVE', 'STOPPED'
    time_remaining: Optional[int] = None  # seconds remaining, None if not active
    message: Optional[str] = None

    class Config:
        from_attributes = True
