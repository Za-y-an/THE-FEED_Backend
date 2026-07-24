from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    username: Optional[str] = Field(default=None, description="Optional. Auto-generated if blank.")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

class ForgotPassword(BaseModel):
    identifier: str = Field(..., description="Enter your email or username")

class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=6)