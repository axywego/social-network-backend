import zlib
from uuid import UUID

from app.database.session_db import get_db
from app.models.friendship import Friendship
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session


def get_ordered_pair(id1, id2):
    return (id1, id2) if id1 < id2 else (id2, id1)


def compress_message(msg: str) -> bytes:
    return zlib.compress(msg.encode("utf-8"), level=6)


def decompress_message(bytes_msg: bytes) -> str:
    return zlib.decompress(bytes_msg).decode("utf-8")


def get_friends(user_id: str, db: Session) -> list[str]:
    friendships = (
        db.query(Friendship)
        .filter(
            or_(Friendship.user1 == UUID(user_id), Friendship.user2 == UUID(user_id)),
            Friendship.status == "accepted",
        )
        .all()
    )

    return [
        str(f.user2) if f.user1 == UUID(user_id) else str(f.user1) for f in friendships
    ]
