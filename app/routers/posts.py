import os
import uuid
from datetime import datetime

from app.core.dependencies import get_current_user
from app.database.session_db import get_db
from app.models.friendship import Friendship
from app.models.post import Post
from app.models.post_comment import PostComment
from app.models.post_like import PostLike
from app.models.user import User
from app.schemes.posts import (
    PostCommentCreate,
    PostCommentOut,
    PostCreate,
    PostOut,
    PostUpdate,
)
from app.ws.manager import manager
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

router = APIRouter(prefix="/posts", tags=["posts"])

POSTS_IMAGES_DIR = "app/static/posts"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def get_post_out(post: Post, db: Session, current_user: User) -> PostOut:
    comments = (
        db.query(PostComment)
        .filter(PostComment.post_id == post.id)
        .order_by(PostComment.created_at.desc())
        .all()
    )

    author = db.query(User).filter(User.id == post.user_id).first()

    likes = db.query(PostLike).filter(PostLike.post_id == post.id).count()

    liked_by_me = (
        db.query(PostLike)
        .filter(PostLike.post_id == post.id, PostLike.user_id == current_user.id)
        .first()
        is not None
    )

    comments_out = [
        PostCommentOut(
            author=db.query(User).filter(User.id == c.user_id).first(),
            content=c.content,
            created_at=c.created_at,
        )
        for c in comments
    ]

    return PostOut(
        id=post.id,
        author=author,
        content=post.content,
        image_url=post.image_url,
        created_at=post.created_at,
        comments=comments_out,
        likes=likes,
        liked_by_me=liked_by_me,
    )


def build_post_image_url(post_id: int, filename: str | None) -> str | None:
    return f"/posts/{post_id}/images/{filename}" if filename else None


@router.get("/count/{user_id}")
def get_user_posts(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Post)
        .filter(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .count()
    )


@router.get("/{post_id}/images/{filename}")
def get_post_image(post_id: int, filename: str, db: Session = Depends(get_db)):
    filename = os.path.basename(filename)
    filepath = os.path.join(POSTS_IMAGES_DIR, str(post_id), filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath)


@router.post("/{post_id}/images")
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    filepath = os.path.join(POSTS_IMAGES_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    post.image_url = f"/static/posts/{filename}"
    db.commit()

    return {"filename": post.image_url}


@router.delete("/{post_id}/delete")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You haven't access to delete this post"
        )

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successful"}


@router.delete("/{post_id}/unlike")
def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    liked_post = (
        db.query(PostLike)
        .filter(PostLike.post_id == post.id, PostLike.user_id == current_user.id)
        .first()
    )

    if not liked_post:
        raise HTTPException(status_code=400, detail="Post already unliked")

    db.delete(liked_post)
    db.commit()

    return {"message": "Post unliked successful"}


@router.post("/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    liked_post = (
        db.query(PostLike)
        .filter(PostLike.post_id == post.id, PostLike.user_id == current_user.id)
        .first()
    )

    if liked_post:
        raise HTTPException(status_code=400, detail="Post already liked")

    new_like = PostLike(post_id=post.id, user_id=current_user.id)
    db.add(new_like)
    db.commit()

    other_user_id = db.query(User).filter(User.id == post.user_id).first().id
    if other_user_id != current_user.id:
        await manager.send_to_user(
            str(),
            {
                "type": "new_like",
                "like_author": f"{current_user.first_name} {current_user.last_name}",
                "message": f"Вам поставили лайк на пост от {post.created_at}",
            },
        )

    return {"message": "Post liked successful"}


@router.post("/create_comment", response_model=PostCommentOut)
async def create_comment(
    payload: PostCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.content:
        raise HTTPException(status_code=400, detail="content is required")

    post = db.query(Post).filter(Post.id == payload.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = PostComment(
        post_id=payload.post_id, user_id=current_user.id, content=payload.content
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    other_user_id = db.query(User).filter(User.id == post.user_id).first().id
    if other_user_id != current_user.id:
        await manager.send_to_user(
            str(db.query(User).filter(User.id == post.user_id).first().id),
            {
                "type": "new_comment",
                "comment_author": f"{current_user.first_name} {current_user.last_name}",
                "message": f"Вам отправлен комментарий на пост от {post.created_at}",
            },
        )

    return PostCommentOut(
        author=current_user,
        content=new_comment.content,
        created_at=new_comment.created_at,
    )


@router.put("/update/{post_id}", response_model=PostOut)
def update_post(
    post_id: int,
    payload: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.content and not payload.image_url:
        raise HTTPException(status_code=400, detail="Content or image is required")

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.content = payload.content
    post.image_url = payload.image_url

    db.commit()
    db.refresh(post)

    return get_post_out(post, db, current_user)


@router.post("/create_post", response_model=PostOut)
def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.content and not payload.image_url:
        raise HTTPException(status_code=400, detail="Content or image is required")

    new_post = Post(
        user_id=current_user.id, content=payload.content, image_url=payload.image_url
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return get_post_out(new_post, db, current_user)


@router.get("/recent", response_model=list[PostOut])
def get_recent_posts(
    limit: int = Query(15, le=50),
    before: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friendships = (
        db.query(Friendship)
        .filter(
            or_(
                and_(
                    or_(
                        Friendship.user1 == current_user.id,
                        Friendship.user2 == current_user.id,
                    ),
                    Friendship.status == "accepted",
                ),
                Friendship.initiator == current_user.id,
            ),
        )
        .all()
    )

    ids = [f.user2 if f.user1 == current_user.id else f.user1 for f in friendships]
    ids.append(current_user.id)

    query = db.query(Post).filter(Post.user_id.in_(ids))
    if before:
        query = query.filter(Post.created_at < before)

    posts = query.order_by(Post.created_at.desc()).limit(limit).all()

    return [get_post_out(p, db, current_user) for p in posts]


@router.get("/me", response_model=list[PostOut])
def get_my_posts(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    posts = (
        db.query(Post)
        .filter(Post.user_id == current_user.id)
        .order_by(Post.created_at.desc())
        .all()
    )
    return [get_post_out(p, db, current_user) for p in posts]


@router.get("/{user_id}", response_model=list[PostOut])
def get_user_posts(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    posts = (
        db.query(Post)
        .filter(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .all()
    )
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    return [get_post_out(p, db, current_user) for p in posts]
