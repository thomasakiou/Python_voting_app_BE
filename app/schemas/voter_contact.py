from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class VoterContactLookupRequest(BaseModel):
    username: str


class VoterContactLookupResponse(BaseModel):
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    masked_email: Optional[str] = None
    masked_phone: Optional[str] = None
    staff_file_no: Optional[str] = None
    staff_station: Optional[str] = None
    staff_rank: Optional[str] = None
    staff_conraiss: Optional[str] = None
    staff_active: Optional[bool] = True
    has_email: bool
    has_phone: bool
    is_accredited: bool
    is_active: bool
    message: Optional[str] = None


class VoterContactSendOTPRequest(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class VoterContactVerifyOTPRequest(BaseModel):
    username: str
    otp_code: str


class VoterDisputeCreateRequest(BaseModel):
    username: str
    dispute_type: str = "CONTACT_UPDATE"
    requested_email: Optional[EmailStr] = None
    requested_phone: Optional[str] = None
    reason: str


class VoterDisputeResolveRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    admin_notes: Optional[str] = None


class VoterDisputeOut(BaseModel):
    id: int
    user_id: int
    username: str
    full_name: str
    current_email: Optional[str] = None
    current_phone: Optional[str] = None
    requested_email: Optional[str] = None
    requested_phone: Optional[str] = None
    dispute_type: str
    reason: str
    status: str
    admin_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
