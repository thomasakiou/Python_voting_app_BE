from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Voter election day login: username (4-digit MCS number). Optional phone for backwards compatibility."""
    username: str
    phone: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    """Voter submits username + the 6-digit OTP."""
    username: str
    otp_code: str


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
    message: Optional[str] = None


class AccreditationSendOTPRequest(BaseModel):
    """Step 2: Voter confirms details and requests OTP for pre-registered email."""
    username: str
    phone: Optional[str] = None
    email: Optional[str] = None


class AccreditationVerifyOTPRequest(BaseModel):
    """Step 3: Voter submits OTP code to complete accreditation."""
    username: str
    otp_code: str
    phone: Optional[str] = None
    email: Optional[str] = None
