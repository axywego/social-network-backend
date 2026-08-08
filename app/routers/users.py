from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database.session_db import get_db
from app.models.user import User

from app.schemas.users import UserOut, UserChange

from app.core.dependencies import get_current_user

import os

import uuid

router = APIRouter(prefix="/users", tags=["users"])

AVATAR_DIR = "app/static/avatars"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024

os.makedirs(AVATAR_DIR, exist_ok=True)

@router.patch("/me/change_avatar")
async def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(AVATAR_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    if current_user.avatar_url:
        old_path = current_user.avatar_url.replace("/static/avatars/", f"{AVATAR_DIR}/")
        if os.path.exists(old_path):
            os.remove(old_path)

    current_user.avatar_url = f"/static/avatars/{filename}"
    db.commit()

    return {"avatar_url": current_user.avatar_url}

@router.put("/me/change_info", response_model=UserOut)
def change_info(payload: UserChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.first_name = payload.first_name
    current_user.last_name = payload.last_name
    current_user.patronymic = payload.patronymic
    current_user.bio = payload.bio
    current_user.birthday = payload.birthday

    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.get("", response_model=list[UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

