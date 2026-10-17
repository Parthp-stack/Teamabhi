from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "STUDENT"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

class VerifyEmailRequest(BaseModel):
    email: str
    role: Optional[str] = None

class VerifyEmailResponse(BaseModel):
    exists: bool
    email: str
    name: str
    role: str
    message: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    role: Optional[str] = None

class ResetPasswordResponse(BaseModel):
    success: bool
    message: str
    email: str
    role: str

