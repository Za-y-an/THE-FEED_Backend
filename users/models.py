# users/models.py
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    display_name: Mapped[str] = mapped_column(String, nullable=False, default="Unknown User") 
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    
    emoji_avatar: Mapped[str] = mapped_column(String, default="🧑‍💻")
    is_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # OTP & Verification Tracking
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_otp: Mapped[str | None] = mapped_column(String, nullable=True)
    reset_otp: Mapped[str | None] = mapped_column(String, nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Security limits (Brute-force protection)
    failed_otp_attempts: Mapped[int] = mapped_column(Integer, default=0)
    lockout_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)