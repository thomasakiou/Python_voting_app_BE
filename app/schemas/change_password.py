from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from typing import List

# ===============================
# CHANGE PASSWORD
# ===============================
class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

