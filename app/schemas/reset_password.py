from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from typing import List

# ===============================
# LOGIN
# ===============================
class UserLogin(BaseModel):
    username: str
    password: str   