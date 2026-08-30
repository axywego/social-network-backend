from uuid import UUID

from app.core.dependencies import get_current_user
from app.core.utils import get_ordered_pair
from app.database.session_db import get_db
from app.models.friendship import Friendship
from app.models.user import User
from app.schemes.friends import FriendOut, FriendRequest, FriendRequestOut
from app.ws.manager import manager
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post("/send_request")
async def send_friend_request(
    payload: FriendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    finded_user = db.query(User).filter(User.username == payload.target_login).first()

    if not finded_user:
        raise HTTPException(status_code=400, detail="Cannot find that username")

    if finded_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself")

    min_user, max_user = get_ordered_pair(current_user.id, finded_user.id)

    existing = (
        db.query(Friendship)
        .filter(Friendship.user1 == min_user, Friendship.user2 == max_user)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400, detail="Friendship already exists or pending"
        )

    pending_request = Friendship(
        user1=min_user, user2=max_user, initiator=current_user.id, status="pending"
    )

    db.add(pending_request)
    db.commit()

    await manager.send_to_user(
        str(finded_user.id),
        {
            "type": "new_friend",
            "sender_name": f"{current_user.first_name} {current_user.last_name}",
            "message": "Вам отправили новый запрос дружбы!",
        },
    )

    return {"message": "Friend request sended successful"}


@router.put("/accept_request")
async def accept_request(
    payload: FriendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    finded_user = db.query(User).filter(User.username == payload.target_login).first()

    if not finded_user:
        raise HTTPException(status_code=400, detail="Cannot find that username")

    min_user, max_user = get_ordered_pair(current_user.id, finded_user.id)

    finded_friendship = (
        db.query(Friendship)
        .filter(
            Friendship.user1 == min_user,
            Friendship.user2 == max_user,
            Friendship.initiator == finded_user.id,
            Friendship.status == "pending",
        )
        .first()
    )

    if not finded_friendship:
        raise HTTPException(status_code=400, detail="Cannot find that friendship")

    finded_friendship.status = "accepted"
    db.commit()

    await manager.send_to_user(
        str(finded_user.id),
        {
            "type": "new_friend",
            "sender_name": f"{current_user.first_name} {current_user.last_name}",
            "message": "Ваш запрос дружбы был одобрен!",
        },
    )

    return {"message": "Friendship was created successful"}


@router.delete("/decline_request")
async def decline_request(
    payload: FriendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    finded_user = db.query(User).filter(User.username == payload.target_login).first()

    if not finded_user:
        raise HTTPException(status_code=400, detail="Cannot find that username")

    min_user, max_user = get_ordered_pair(current_user.id, finded_user.id)

    finded_friendship = (
        db.query(Friendship)
        .filter(
            Friendship.user1 == min_user,
            Friendship.user2 == max_user,
            Friendship.status == "pending",
        )
        .first()
    )

    if not finded_friendship:
        raise HTTPException(status_code=400, detail="Cannot find that friendship")

    db.delete(finded_friendship)
    db.commit()

    await manager.send_to_user(
        str(finded_user.id),
        {
            "type": "new_friend",
            "sender_name": f"{current_user.first_name} {current_user.last_name}",
            "message": "Ваш запрос дружбы был отклонен!",
        },
    )

    return {"message": "friendship was declined successful"}


@router.delete("/remove_friend")
def remove_friend(
    payload: FriendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    finded_user = db.query(User).filter(User.username == payload.target_login).first()

    if not finded_user:
        raise HTTPException(status_code=400, detail="Cannot find that username")

    min_user, max_user = get_ordered_pair(current_user.id, finded_user.id)

    finded_friendship = (
        db.query(Friendship)
        .filter(
            Friendship.user1 == min_user,
            Friendship.user2 == max_user,
            Friendship.status == "accepted",
        )
        .first()
    )

    if not finded_friendship:
        raise HTTPException(status_code=400, detail="Cannot find that friendship")

    # db.delete(finded_friendship)

    finded_friendship.initiator = finded_user.id
    finded_friendship.status = "pending"
    db.commit()

    db.commit()

    return {"message": "friend removed successful"}


@router.get("/incoming_requests", response_model=list[FriendRequestOut])
def get_incoming_requests(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    friendships = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.user1 == current_user.id,
                Friendship.user2 == current_user.id,
            ),
            Friendship.status == "pending",
            Friendship.initiator != current_user.id,
        )
        .all()
    )

    result = []
    for f in friendships:
        other_id = f.user2 if f.user1 == current_user.id else f.user1
        other_user = db.query(User).filter(User.id == other_id).first()
        if other_user:
            result.append(
                FriendRequestOut(
                    user=FriendOut(
                        id=other_user.id,
                        username=other_user.username,
                        first_name=other_user.first_name,
                        last_name=other_user.last_name,
                        avatar_url=other_user.avatar_url,
                    ),
                    created_at=f.created_at,
                )
            )

    return result


@router.get("/outgoing_requests", response_model=list[FriendRequestOut])
def get_outgoing_requests(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    friendships = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.user1 == current_user.id,
                Friendship.user2 == current_user.id,
            ),
            Friendship.status == "pending",
            Friendship.initiator == current_user.id,
        )
        .all()
    )

    result = []
    for f in friendships:
        other_id = f.user2 if f.user1 == current_user.id else f.user1
        other_user = db.query(User).filter(User.id == other_id).first()
        if other_user:
            result.append(
                FriendRequestOut(
                    user=FriendOut(
                        id=other_user.id,
                        username=other_user.username,
                        first_name=other_user.first_name,
                        last_name=other_user.last_name,
                        avatar_url=other_user.avatar_url,
                    ),
                    created_at=f.created_at,
                )
            )

    return result


@router.get("/count/{user_id}")
def get_friend_count(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friendships = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.user1 == user_id,
                Friendship.user2 == user_id,
            ),
            Friendship.status == "accepted",
        )
        .all()
    )

    friend_ids = [f.user2 if f.user1 == user_id else f.user1 for f in friendships]

    friend_count = db.query(User).filter(User.id.in_(friend_ids)).count()
    return friend_count


@router.get("/list/{user_id}", response_model=list[FriendOut])
def get_friend_list(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friendships = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.user1 == user_id,
                Friendship.user2 == user_id,
            ),
            Friendship.status == "accepted",
        )
        .all()
    )

    friend_ids = [f.user2 if f.user1 == user_id else f.user1 for f in friendships]

    friends = db.query(User).filter(User.id.in_(friend_ids)).all()
    return friends
