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

class ForgotPasswordRequest(BaseModel):
    email: str
    role: Optional[str] = None

class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str
    email: str
    role: Optional[str] = None
    demo_otp: Optional[str] = None
    reset_link: Optional[str] = None

class VerifyResetTokenResponse(BaseModel):
    valid: bool
    email: str
    name: str
    role: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str
    role: Optional[str] = None

VerifyResetOTPRequest = VerifyOTPRequest

class VerifyOTPResponse(BaseModel):
    verified: bool = True
    success: bool = True
    message: str = "OTP verified successfully"
    email: str
    role: Optional[str] = None
    reset_token: Optional[str] = None

VerifyResetOTPResponse = VerifyOTPResponse

class ResetPasswordRequest(BaseModel):
    token: Optional[str] = None
    new_password: str
    confirm_password: Optional[str] = None
    email: Optional[str] = None
    otp: Optional[str] = None
    role: Optional[str] = None

class ResetPasswordResponse(BaseModel):
    success: bool
    message: str
    email: str
    role: str

