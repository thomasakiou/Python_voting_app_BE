from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OfficeBase(BaseModel):
    office_code: str
    description: str
    max_votes: Optional[int] = 1
    is_disqualified: Optional[bool] = False

    class Config:
        from_attributes = True


class OfficeCreate(OfficeBase):
    max_votes: Optional[int] = 1

    class Config:
        from_attributes = True


class OfficeResponse(OfficeBase):
    id: int
    max_votes: int = 1
    created_at: datetime

    class Config:
        from_attributes = True


class OfficeUpdate(BaseModel):
    office_code: Optional[str] = None
    description: Optional[str] = None
    max_votes: Optional[int] = None
    is_disqualified: Optional[bool] = None

    class Config:
        from_attributes = True


class OfficeOut(BaseModel):
    office_code: str
    description: str
    max_votes: Optional[int] = 1
    is_disqualified: Optional[bool] = False

    class Config:
        from_attributes = True


class OfficeDisqualifyRequest(BaseModel):
    is_disqualified: bool
