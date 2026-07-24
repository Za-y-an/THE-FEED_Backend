# users/router.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from users.models import User
from posts.schemas import UserBasicInfo
from auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users & Profile"])

@router.get("/me", response_model=UserBasicInfo)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Fetches the profile details of the currently logged-in user."""
    return UserBasicInfo(
        username=current_user.username,
        emoji_avatar=current_user.emoji_avatar,
        is_ai=current_user.is_ai
    )

@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_my_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently deletes the user account.
    Thanks to our SQL 'CASCADE' constraints, this also instantly wipes all 
    their posts, comments, and reactions from the database.
    """
    await db.delete(current_user)
    await db.commit()
    
    return {"message": "Account and all associated data have been permanently deleted."}