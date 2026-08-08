from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session_db import get_db
from app.models.user import User
from app.models.friendship import Friendship
from app.models.post import Post
from app.models.post_comment import PostComment
from app.schemas.posts import PostCommentCreate, PostCreate, PostOut

from app.core.dependencies import get_current_user

from app.core.utils import get_ordered_pair

import os

import uuid

import datetime

router = APIRouter(prefix="/posts", tags=["posts"])

POSTS_IMAGES_URL = "app/static/posts"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024

def build_post_image_url(post_id: int, filename: str | None) -> str | None:
    return f"/posts/{post_id}/images/{filename}" if filename else None

@router.get("/{post_id}/images/{filename}")
def get_post_image(post_id: int, filename: str, db: Session = Depends(get_db)):
    filename = os.path.basename(filename)
    filepath = os.path.join(POSTS_IMAGES_URL, str(post_id), filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath)

@router.post("/{post_id}/images")
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    filename = f"{uuid.uuid4()}{ext}"
    post_dir = os.path.join(POSTS_IMAGES_URL, str(post_id))
    os.makedirs(post_dir, exist_ok=True)

    filepath = os.path.join(post_dir, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    post.image_url = filename
    db.commit()

    return {"filename": filename}

@router.post("/create_post")
def create_post(payload: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not payload.content and not payload.image_url:
        raise HTTPException(status_code=400, detail="content or image is required")
    
    new_post = Post(
        user_id=current_user.id,
        content=payload.content,
        image_url=payload.image_url
    )

    db.add(new_post)
    db.commit()

    return {"message": "Post created successful"}

@router.post("/create_comment")
def create_comment(payload: PostCommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not payload.content and not payload.image_url:
        raise HTTPException(status_code=400, detail="content or image is required")
    
    post = db.query(Post).filter(Post.id == payload.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = PostComment(
        post_id=payload.post_id,
        user_id=current_user.id,
        content=payload.content,
        image_url=payload.image_url
    )

    db.add(new_comment)
    db.commit()

    return {"message": "Comment created successful"}

@router.get("/recent", response_model=list[PostOut])
def get_recent_posts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    friendships = db.query(Friendship).filter(
        or_(
            and_(
                or_(
                    Friendship.user1 == current_user.id, 
                    Friendship.user2 == current_user.id
                ),
                Friendship.status == "accepted"
            ),
            Friendship.initiator == current_user.id
        ),

    ).all()

    friend_ids = [f.user2 if f.user1 == current_user.id else f.user1 for f in friendships]

    posts = db.query(Post).filter(Post.user_id.in_(friend_ids)).order_by(Post.created_at.desc()).all()

    return [
        PostOut(
            post_id=p.id,
            user_id=p.user_id,
            content=p.content,
            image_url=build_post_image_url(p.id, p.image_url),
            created_at=p.created_at
        )
        for p in posts
    ]

@router.get("/me", response_model=list[PostOut])
def get_my_posts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.user_id == current_user.id).order_by(Post.created_at.desc()).all()
    return [
        PostOut(
            post_id=p.id,
            user_id=p.user_id,
            content=p.content,
            image_url=build_post_image_url(p.id, p.image_url),
            created_at=p.created_at
        )
        for p in posts
    ]

@router.get("/{user_id}", response_model=list[PostOut])
def get_user_posts(user_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at.desc()).all()
    return [
        PostOut(
            post_id=p.id,
            user_id=p.user_id,
            content=p.content,
            image_url=build_post_image_url(p.id, p.image_url),
            created_at=p.created_at
        )
        for p in posts
    ]