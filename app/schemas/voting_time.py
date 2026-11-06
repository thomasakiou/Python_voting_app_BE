from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


# ===============================================================================================
# VOTING TIME SCHEMA
# ===============================================================================================
class VotingTimeBase(BaseModel):
    start_time: datetime
    end_time: datetime
    
    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
    class Config:
        from_attributes = True


class VotingTimeCreate(VotingTimeBase):
    class Config:
        from_attributes = True


class VotingTimeUpdate(VotingTimeBase):
    class Config:
        from_attributes = True


class VotingTimeResponse(VotingTimeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VotingTimeOut(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime
    is_active: bool
    time_remaining: Optional[int] = None  # seconds remaining, None if not active
    
    class Config:
        from_attributes = True
