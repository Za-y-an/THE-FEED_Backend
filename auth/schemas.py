# auth/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, description="The user's real or display name")
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    username: Optional[str] = Field(default=None, description="Optional. Auto-generated if blank.")

    @field_validator('email', mode='after')
    @classmethod
    def prevent_email_typos(cls, v: str) -> str:
        email_str = str(v).lower()
        if email_str.endswith('@gmail.co'):
            raise ValueError("Invalid email provider. Did you mean @gmail.com?")
        if email_str.endswith('@yahoo.co'):
            raise ValueError("Invalid email provider. Did you mean @yahoo.com?")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email', mode='after')
    @classmethod
    def prevent_email_typos(cls, v: str) -> str:
        email_str = str(v).lower()
        if email_str.endswith('@gmail.co'):
            raise ValueError("Invalid email provider. Did you mean @gmail.com?")
        return v

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

class ForgotPassword(BaseModel):
    identifier: str = Field(..., description="Enter your email or username")

class ResetPassword(BaseModel):
    identifier: str = Field(..., description="Email or Username")
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=6)

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)