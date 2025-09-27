from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ===============================================================================================
# OFFICE SCHEMA
# ===============================================================================================
class OfficeBase(BaseModel):
    office_code: str
    description: str
    class config:
        orm_mode = True
  

class OfficeCreate(OfficeBase):
    # office_code: str
    # description: str
    class config:
        orm_mode = True

class OfficeResponse(OfficeBase):
    id: int
    created_at: datetime
    class config:
        orm_mode = True
 
class OfficeUpdate(OfficeBase):
    class config:
        orm_mode = True
 
class OfficeOut(BaseModel):
    office_code: str
    description: str
    class config:
       orm_mode = True