# users/router.py
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from core.database import get_db
from users.models import User
from posts.schemas import UserBasicInfo
from auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users & Profile"])

# NEW: Schema to validate incoming profile updates
class UserUpdate(BaseModel):
    display_name: str = Field(min_length=1)
    username: str = Field(min_length=1)
    emoji_avatar: str = Field(min_length=1)

@router.get("/me", response_model=UserBasicInfo)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Fetches the profile details of the currently logged-in user."""
    return UserBasicInfo(
        display_name=current_user.display_name,
        username=current_user.username,
        emoji_avatar=current_user.emoji_avatar,
        is_ai=current_user.is_ai
    )

# NEW: Endpoint to permanently save profile edits
@router.put("/me", response_model=UserBasicInfo)
async def update_my_profile(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if they are trying to take a username that someone else already owns
    if update_data.username != current_user.username:
        result = await db.execute(select(User).where(User.username == update_data.username))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Username is already taken")
    
    # Apply the new changes
    current_user.display_name = update_data.display_name
    current_user.username = update_data.username
    current_user.emoji_avatar = update_data.emoji_avatar
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserBasicInfo(
        display_name=current_user.display_name,
        username=current_user.username,
        emoji_avatar=current_user.emoji_avatar,
        is_ai=current_user.is_ai
    )

@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_my_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await db.delete(current_user)
    await db.commit()
    return {"message": "Account and all associated data have been permanently deleted."}