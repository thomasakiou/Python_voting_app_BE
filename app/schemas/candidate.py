from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..schemas.office import OfficeOut
# from pydantic.types import conint


# ===============================================================================================
# OFFICE SCHEMA
# ===============================================================================================
class CandidateBase(BaseModel):
    candidate_code: str
    name: str
    class config:
        orm_mode = True

class CandidateCreate(CandidateBase):
    office_code: str
    # candidate_code: str
    # name: str
    # contested_position: str
    class config:
        orm_mode = True

class CandidateResponse(CandidateBase):
    id: int
    # candidate_code: str
    # name: str
    created_at: datetime
    office: OfficeOut
    class config:
        orm_mode = True
