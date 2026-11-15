from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..schemas.office import OfficeOut


class CandidateBase(BaseModel):
    candidate_code: str
    name: str
    image_url: Optional[str] = None
    is_disqualified: Optional[bool] = False
    is_hidden: Optional[bool] = False
    manifesto_title: Optional[str] = None
    manifesto: Optional[str] = None
    mcs_number: Optional[str] = None
    conraiss: Optional[str] = None
    station: Optional[str] = None
    file_no: Optional[str] = None

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
    vote_count: Optional[int] = 0

    class Config:
        from_attributes = True


class CandidateDisqualifyRequest(BaseModel):
    is_disqualified: bool


class CandidateHideRequest(BaseModel):
    is_hidden: bool


class BulkCandidateStatusRequest(BaseModel):
    candidate_ids: List[int]
    is_disqualified: bool


class BulkCandidateVisibilityRequest(BaseModel):
    candidate_ids: List[int]
    is_hidden: bool


class BulkCandidateDeleteRequest(BaseModel):
    candidate_ids: List[int]
