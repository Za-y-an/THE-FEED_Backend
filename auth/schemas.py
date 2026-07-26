# auth/schemas.py
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, description="The user's real or display name")
    username: str = Field(min_length=1, description="Required username")
    password: str = Field(min_length=8, description="Password must be at least 8 characters")

    @field_validator('email', mode='after')
    @classmethod
    def prevent_email_typos(cls, v: str) -> str:
        email_str = str(v).lower()
        if email_str.endswith('@gmail.co'):
            raise ValueError("Invalid email provider. Did you mean @gmail.com?")
        if email_str.endswith('@yahoo.co'):
            raise ValueError("Invalid email provider. Did you mean @yahoo.com?")
        return v

    @field_validator('password', mode='after')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        # Check for at least one alphabet letter (a-z, A-Z)
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Password must contain at least one alphabet letter.")
        # Check for at least one non-alphabet character (number, space, or special symbol)
        if not re.search(r'[^a-zA-Z]', v):
            raise ValueError("Password must contain at least one number, space, or special character.")
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
    new_password: str = Field(min_length=8)

    @field_validator('new_password', mode='after')
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Password must contain at least one alphabet letter.")
        if not re.search(r'[^a-zA-Z]', v):
            raise ValueError("Password must contain at least one number, space, or special character.")
        return v


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)