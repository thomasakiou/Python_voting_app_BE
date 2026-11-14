from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from typing import List

# ===============================
# TOKEN
# ===============================
class Token(BaseModel):
    access_token: str
    token_type: str
    fullname: str
    role: Optional[str] = None
    username: Optional[str] = None


class TokenData(BaseModel):
    id: int | None = None
    role: str | None = None
    session_id: str | None = None
