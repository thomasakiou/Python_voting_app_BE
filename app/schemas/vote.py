from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
    office_code: Optional[str] = None
    candidate_code: Optional[str] = None
    receipt_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MyVoteResponse(BaseModel):
    id: int
    office_code: str
    office_name: str
    candidate_code: str
    candidate_name: str
    receipt_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
