from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OfficeBase(BaseModel):
    office_code: str
    description: str
    is_disqualified: Optional[bool] = False

    class Config:
        from_attributes = True


class OfficeCreate(OfficeBase):
    class Config:
        from_attributes = True


class OfficeResponse(OfficeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OfficeUpdate(BaseModel):
    office_code: Optional[str] = None
    description: Optional[str] = None
    is_disqualified: Optional[bool] = None

    class Config:
        from_attributes = True


class OfficeOut(BaseModel):
    office_code: str
    description: str
    is_disqualified: Optional[bool] = False

    class Config:
        from_attributes = True


class OfficeDisqualifyRequest(BaseModel):
    is_disqualified: bool
