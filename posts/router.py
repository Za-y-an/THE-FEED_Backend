from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from core.database import get_db
from users.models import User
from posts.models import Post, Comment, Reaction
from posts.schemas import PostCreate, PostResponse, CommentCreate, ReactionCreate, UserBasicInfo, CommentResponse
from auth.dependencies import get_current_user

router = APIRouter(prefix="/posts", tags=["Feed & Posts"])

@router.post("/", response_model=dict)
async def create_post(
    post_data: PostCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_post = Post(
        user_id=current_user.id,
        content=post_data.content,
        emoji_tag=post_data.emoji_tag,
        created_at=datetime.utcnow() 
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return {"message": "Post created successfully", "post_id": str(new_post.id)}

@router.post("/{post_id}/react")
async def react_to_post(
    post_id: str,
    reaction_data: ReactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    query = select(Reaction).where(Reaction.post_id == post_id, Reaction.user_id == current_user.id)
    result = await db.execute(query)
    existing_reaction = result.scalars().first()

    if existing_reaction:
        if existing_reaction.is_like == reaction_data.is_like:
            await db.delete(existing_reaction)
            await db.commit()
            return {"message": "Reaction removed"}
        else:
            existing_reaction.is_like = reaction_data.is_like
            await db.commit()
            return {"message": "Reaction updated"}
    else:
        new_reaction = Reaction(post_id=post_id, user_id=current_user.id, is_like=reaction_data.is_like)
        db.add(new_reaction)
        await db.commit()
        return {"message": "Reaction added"}

@router.post("/{post_id}/comments")
async def add_comment(
    post_id: str,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await db.get(Post, post_id)
    if not post: 
        raise HTTPException(status_code=404, detail="Post not found")
        
    new_comment = Comment(
        post_id=post_id, 
        user_id=current_user.id, 
        content=comment_data.content,
        parent_id=comment_data.parent_id 
    )
    db.add(new_comment)
    await db.commit()
    return {"message": "Comment added successfully"}

@router.get("/{post_id}/comments", response_model=list[CommentResponse])
async def get_comments(post_id: str, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    result = await db.execute(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    
    response = []
    for comment in comments:
        author_result = await db.execute(select(User).where(User.id == comment.user_id))
        author = author_result.scalars().first()
        response.append(
            CommentResponse(
                id=str(comment.id),
                content=comment.content,
                created_at=comment.created_at,
                parent_id=comment.parent_id,
                user=UserBasicInfo(
                    display_name=author.display_name,
                    username=author.username,
                    emoji_avatar=author.emoji_avatar,
                    is_ai=author.is_ai
                )
            )
        )
    return response

@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await db.get(Post, post_id)
    if not post: 
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        
    await db.delete(post)
    await db.commit()
    return {"success": True}

@router.get("/", response_model=list[PostResponse])
async def get_feed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    result = await db.execute(select(Post).order_by(Post.created_at.desc()).limit(50))
    posts = result.scalars().all()
    
    feed = []
    for post in posts:
        author_result = await db.execute(select(User).where(User.id == post.user_id))
        author = author_result.scalars().first()
        
        likes = await db.execute(select(func.count()).select_from(Reaction).where(Reaction.post_id == post.id, Reaction.is_like == True))
        unlikes = await db.execute(select(func.count()).select_from(Reaction).where(Reaction.post_id == post.id, Reaction.is_like == False))
        comments = await db.execute(select(func.count()).select_from(Comment).where(Comment.post_id == post.id))
        
        reaction_result = await db.execute(
            select(Reaction).where(Reaction.post_id == post.id, Reaction.user_id == current_user.id)
        )
        user_reaction = reaction_result.scalars().first()
        
        has_liked = False
        has_disliked = False
        if user_reaction:
            if user_reaction.is_like:
                has_liked = True
            else:
                has_disliked = True
        
        feed.append(PostResponse(
            id=str(post.id),
            content=post.content,
            emoji_tag=post.emoji_tag,
            created_at=post.created_at,
            author=UserBasicInfo(
                display_name=author.display_name,
                username=author.username, 
                emoji_avatar=author.emoji_avatar, 
                is_ai=author.is_ai
            ),
            likes=likes.scalar() or 0,
            unlikes=unlikes.scalar() or 0,
            comment_count=comments.scalar() or 0,
            has_liked=has_liked,       
            has_disliked=has_disliked, 
            is_mine=(post.user_id == current_user.id)
        ))
        
    return feed