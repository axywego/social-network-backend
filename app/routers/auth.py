from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.session_db import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken

from app.schemas.auth import UserRegister, UserLogin, AccessTokenResponse, RefreshRequest

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token

import hashlib

from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == payload.username).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        username = payload.username,
        password_hash = hash_password(payload.password),

        first_name = payload.first_name,
        last_name = payload.last_name,
        patronymic = payload.patronymic,
        birthday = payload.birthday
    )

    db.add(new_user)
    db.commit()

    return {"message": "Registration was successful"}

@router.post("/login", response_model=AccessTokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token({"sub": str(user.id)})
    raw_refresh_token, hashed_refresh_token, expires_at = create_refresh_token()

    new_refresh_token = RefreshToken(
        user_id = user.id,
        token_hash = hashed_refresh_token,
        expires_at = expires_at
    )

    db.add(new_refresh_token)
    db.commit()

    return {"access_token": access_token, "refresh_token": raw_refresh_token}

@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()

    stored_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if not stored_token or stored_token.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == stored_token.user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    db.delete(stored_token)

    new_access_token = create_access_token({"sub": str(user.id)})
    raw_refresh_token, hashed_refresh_token, expires_at = create_refresh_token()

    new_refresh_token = RefreshToken(
        user_id = user.id,
        token_hash = hashed_refresh_token,
        expires_at = expires_at
    )

    db.add(new_refresh_token)
    db.commit()

    return {"access_token": new_access_token, "refresh_token": raw_refresh_token}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()

    stored_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if stored_token:
        db.delete(stored_token)
        db.commit()

    return {"message": "Logout was successful"}