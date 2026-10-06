from collections import UserList

from app.core.security import ALGORITHM, SECRET_KEY
from app.database.session_db import get_db
from app.models.ban_reason import BanReason
from app.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

BANNED_DETAIL_CODE = "user_banned"


def ban_detail(user: User, db: Session) -> dict:
    """Reason text travels with the 403 so the client can show it."""
    reason = None
    if user.banned_reason is not None:
        found = db.get(BanReason, user.banned_reason)
        reason = found.note if found else None

    return {"code": BANNED_DETAIL_CODE, "message": "Вы забанены", "reason": reason}


def ensure_not_banned(user: User, db: Session) -> None:
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=ban_detail(user, db)
        )


def get_user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    return db.get(User, user_id)


def get_current_admin(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None or user.role != "admin":
        raise credentials_exception

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    ensure_not_banned(user, db)

    return user
