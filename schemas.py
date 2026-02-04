from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# User (Pydantic models for request/response)
class UserBase(BaseModel):
    user_id: str
    name: str
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Login Request
class UserLogin(BaseModel):
    user_id: str
    password: str

# Token Response
class Token(BaseModel):
    access_token: str
    token_type: str

# Login History
class LoginHistoryBase(BaseModel):
    ip_address: Optional[str] = None
    success: bool

class LoginHistoryCreate(LoginHistoryBase):
    user_id: int

class LoginHistoryResponse(LoginHistoryBase):
    id: int
    login_at: datetime

    class Config:
        from_attributes = True
