from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Step 1: User submits username + phone number to initiate OTP login."""
    username: str
    phone: str


class VerifyOTPRequest(BaseModel):
    """Step 2: User submits username + the OTP they received."""
    username: str
    otp_code: str
