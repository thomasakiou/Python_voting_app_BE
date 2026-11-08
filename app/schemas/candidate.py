from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..schemas.office import OfficeOut


class CandidateBase(BaseModel):
    candidate_code: str
    name: str
    image_url: Optional[str] = None
    is_disqualified: Optional[bool] = False

    class Config:
        from_attributes = True


class CandidateCreate(CandidateBase):
    office_code: str

    class Config:
        from_attributes = True


class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    office: Optional[OfficeOut] = None

    class Config:
        from_attributes = True


class CandidateDisqualifyRequest(BaseModel):
    is_disqualified: bool
