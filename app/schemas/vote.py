from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from pydantic.types import conint


# ========================================
# VOTE SCHEMA
# ========================================
class VoteCreate(BaseModel):
    candidate_code: str
    office_code: str


class VoteResponse(BaseModel):
    id: int
    user_name: str
    candidate_name: str
    office_name: str
    created_at: datetime

    class Config:
        orm_mode = True

