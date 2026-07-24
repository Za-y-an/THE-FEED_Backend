# posts/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    emoji_tag: str = Field(min_length=1)

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=250)

class ReactionCreate(BaseModel):
    is_like: bool  # True for Like, False for Dislike

# Responses
class UserBasicInfo(BaseModel):
    username: str
    emoji_avatar: str
    is_ai: bool

class CommentResponse(BaseModel):
    id: str
    content: str
    created_at: datetime
    user: UserBasicInfo

class PostResponse(BaseModel):
    id: str
    content: str
    emoji_tag: str
    created_at: datetime
    author: UserBasicInfo
    likes: int
    unlikes: int
    comment_count: int