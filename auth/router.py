# auth/router.py
import random
import uuid
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from core.database import get_db
from core.config import settings
from core.security import get_password_hash, verify_password, create_access_token
from users.models import User
from auth.schemas import UserRegister, UserLogin, TokenResponse, ForgotPassword, ResetPassword, VerifyOTP

router = APIRouter(prefix="/auth", tags=["Authentication"])

def send_email_helper(to_email: str, subject: str, body: str):
    sender_email = settings.EMAIL_SENDER  
    sender_password = settings.EMAIL_PASSWORD 
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

async def check_lockout(user: User):
    now = datetime.now(timezone.utc)
    if user.lockout_until and now < user.lockout_until:
        diff = (user.lockout_until - now).total_seconds()
        raise HTTPException(status_code=403, detail=f"Too many failed attempts. Try again in {int(diff)} seconds.")
    if user.lockout_until and now >= user.lockout_until:
        user.lockout_until = None
        user.failed_otp_attempts = 0

async def handle_failed_otp(user: User, db: AsyncSession):
    user.failed_otp_attempts += 1
    if user.failed_otp_attempts >= 3:
        user.lockout_until = datetime.now(timezone.utc) + timedelta(minutes=2)
        await db.commit()
        raise HTTPException(status_code=403, detail="Maximum attempts reached. Account locked for 2 minutes.")
    await db.commit()
    raise HTTPException(status_code=400, detail=f"Invalid code. {3 - user.failed_otp_attempts} attempts remaining.")

@router.post("/register")
async def register(user_data: UserRegister, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalars().first()

    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=90)
    body = f"Welcome to THE FEED. Your verification code is:\n\n{otp}\n\nThis code expires in 1 minute 30 seconds."

    if existing_user:
        if not existing_user.is_verified:
            existing_user.verification_otp = otp
            existing_user.otp_expires_at = expires_at
            existing_user.failed_otp_attempts = 0
            existing_user.lockout_until = None
            existing_user.hashed_password = get_password_hash(user_data.password) 
            await db.commit()
            background_tasks.add_task(send_email_helper, existing_user.email, "THE FEED - Verification Code", body)
            return {"message": "Account exists but is unverified. New OTP sent."}
        raise HTTPException(status_code=400, detail="Email already registered and verified")

    final_username = user_data.username or f"user_{uuid.uuid4().hex[:8]}"
    user_result = await db.execute(select(User).where(User.username == final_username))
    if user_result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        email=user_data.email, username=final_username, display_name=user_data.display_name,
        hashed_password=get_password_hash(user_data.password), is_verified=False,
        verification_otp=otp, otp_expires_at=expires_at, failed_otp_attempts=0
    )
    db.add(new_user)
    await db.commit()

    background_tasks.add_task(send_email_helper, new_user.email, "THE FEED - Verification Code", body)
    return {"message": "Registration successful. Please verify your email with the OTP sent."}

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(data: VerifyOTP, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    await check_lockout(user)

    now = datetime.now(timezone.utc)
    if user.otp_expires_at and now > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired. Register again for a new code.")

    if user.verification_otp != data.otp:
        await handle_failed_otp(user, db)

    user.is_verified = True
    user.verification_otp = None
    user.otp_expires_at = None
    user.failed_otp_attempts = 0
    await db.commit()

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified. Register again to get a new code.")

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    query = select(User).where(or_(User.email == data.identifier, User.username == data.identifier))
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        return {"message": "If an account matches that information, a reset token has been sent."}

    otp = str(random.randint(100000, 999999))
    user.reset_otp = otp
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(seconds=90)
    user.failed_otp_attempts = 0
    user.lockout_until = None
    await db.commit()

    body = f"Your password reset code is:\n\n{otp}\n\nThis code expires in 1 minute 30 seconds."
    background_tasks.add_task(send_email_helper, user.email, "THE FEED - Password Reset Code", body)
    return {"message": "If an account matches that information, a reset token has been sent."}

@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    query = select(User).where(or_(User.email == data.identifier, User.username == data.identifier))
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid account")

    await check_lockout(user)

    now = datetime.now(timezone.utc)
    if user.otp_expires_at and now > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="Reset code has expired. Request a new one.")

    if user.reset_otp != data.otp:
        await handle_failed_otp(user, db)

    user.hashed_password = get_password_hash(data.new_password)
    user.reset_otp = None 
    user.otp_expires_at = None
    user.failed_otp_attempts = 0
    await db.commit()

    return {"message": "Password updated successfully"}