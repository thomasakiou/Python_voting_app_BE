from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from pydantic.types import conint


from enum import Enum as PyEnum

class UserRole(str, PyEnum):
    super_admin = "super-admin"
    admin = "admin"
    voter = "voter"


# ===============================================================================================
# USER SCHEMA
# ===============================================================================================
class UserBase(BaseModel):
    # email: EmailStr
    username: str
    full_name: str
    phone: Optional[str] = None
    # role: UserRole   # 'admin','voter'
    

class UserCreate(BaseModel):
    username: str
    password: str
    class config:
        orm_mode = True

class UserResponse(UserBase):
    id: int
    created_at: datetime
    role: UserRole   # 'admin','voter'
    class config:
        orm_mode = True

class UserOut(UserBase):
    id: int
    username: str
    role: UserRole   # 'admin','voter'
    class config:
        orm_mode = True