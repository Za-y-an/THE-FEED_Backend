# auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from core.database import get_db
from core.security import get_password_hash, verify_password, create_access_token, generate_reset_token
from users.models import User
from auth.schemas import UserRegister, UserLogin, TokenResponse, ForgotPassword, ResetPassword
import uuid

# Email Libraries
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- EMAIL HELPER FUNCTION ---
def send_reset_email(to_email: str, token: str):
    """
    Sends the reset token to the user's email using a live Gmail SMTP server.
    """
    sender_email = "ahaduzzaman.chd@gmail.com"  
    sender_password = "jkaxtyuefbcgvkam" # Spaces removed for standard SMTP formatting

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "THE FEED - Password Reset Token"

    body = f"Your password reset token is:\n\n{token}\n\nCopy and paste this into the app to reset your password. This token will expire soon."
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Standard Gmail SMTP configuration
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"Successfully sent reset email to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
# -----------------------------

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    final_username = user_data.username
    if not final_username:
        final_username = f"user_{uuid.uuid4().hex[:8]}"
    else:
        user_result = await db.execute(select(User).where(User.username == final_username))
        if user_result.scalars().first():
            raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        email=user_data.email,
        username=final_username,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.id})
    return {"access_token": access_token, "token_type": "bearer", "username": new_user.username}

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPassword, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    # Query using SQLAlchemy's or_ function to check BOTH columns
    query = select(User).where(
        or_(User.email == data.identifier, User.username == data.identifier)
    )
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        # Security best practice: Always return 200 so hackers can't guess valid usernames/emails
        return {"message": "If an account matches that information, a reset token has been sent."}

    reset_token = generate_reset_token()
    user.reset_token = reset_token
    await db.commit()

    # Pass the email dispatch off to the background task so the API responds instantly
    background_tasks.add_task(send_reset_email, user.email, reset_token)

    return {"message": "If an account matches that information, a reset token has been sent."}

@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.reset_token == data.token))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None 
    await db.commit()

    return {"message": "Password updated successfully"}