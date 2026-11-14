from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Voter election day login: username (4-digit MCS number). Optional device_id and phone."""
    username: str
    phone: Optional[str] = None
    device_id: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    """Voter submits username + the 6-digit OTP + device_id."""
    username: str
    otp_code: str
    device_id: Optional[str] = None


# Accreditation Schemas
class AccreditationValidateRequest(BaseModel):
    """Step 1: Voter submits 4-digit MCS username to look up name."""
    username: str


class AccreditationValidateResponse(BaseModel):
    username: str
    full_name: str
    is_accredited: bool
    is_active: bool
    phone: Optional[str] = None
    email: Optional[str] = None
    masked_phone: Optional[str] = None
    masked_email: Optional[str] = None
    staff_file_no: Optional[str] = None
    staff_station: Optional[str] = None
    staff_rank: Optional[str] = None
    staff_conraiss: Optional[str] = None
    staff_active: Optional[bool] = True
    message: Optional[str] = None


class ElectionVoterLookupRequest(BaseModel):
    username: str


class ElectionVoterLookupResponse(BaseModel):
    username: str
    full_name: str
    staff_file_no: Optional[str] = None
    staff_station: Optional[str] = None
    staff_rank: Optional[str] = None
    staff_conraiss: Optional[str] = None
    staff_active: Optional[bool] = True
    is_accredited: bool
    is_active: bool
    has_email: bool
    has_phone: bool
    masked_email: Optional[str] = None
    masked_phone: Optional[str] = None
    message: Optional[str] = None


class AccreditationSendOTPRequest(BaseModel):
    """Step 2: Voter confirms details and requests OTP for pre-registered email."""
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None


class AccreditationVerifyOTPRequest(BaseModel):
    """Step 3: Voter submits OTP code to complete accreditation, binding physical device."""
    username: str
    otp_code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    device_id: Optional[str] = None
    device_info: Optional[str] = None
