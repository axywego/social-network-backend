from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.session_db import get_db
from app.models.user import User
from app.models.friendship import Friendship

from app.schemes.friends import FriendRequest, FriendOut, FriendRequestOut

from app.core.dependencies import get_current_user

from app.core.utils import get_ordered_pair

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/send_request")
def send_friend_request(payload: FriendRequest, current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    finded_user = db.query(User).filter(User.username == payload.target_login).first()

    if not finded_user:
        raise HTTPException(status_code=400, detail="Cannot find that username")

    if finded_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send request to yourself")

    min_user, max_user = get_ordered_pair(current_user.id, finded_user.id)

    existing = db.query(Friendship).filter(Friendship.user1 == min_user, Friendship.user2 == max_user).first()

    if existing:
        raise HTTPException(status_code=400, detail="Friendship already exists or pending")

    pending_request = Friendship(
        user1 = min_user,
        user2 = max_user,
        initiator = current_user.id,
        status = "pending"
    )

    db.add(pending_request)
    db.commit()

    return {"message": "Friend request sended successful"}

@router.put("/accept_request")
def accept_request(payload: FriendRequest, current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    finded_user = db.query(User).filter(User.username == payload.target_login).first()

    if not finded_user:
        raise HTTPException(status_code=400, detail="Cannot find that username")

    min_user, max_user = get_ordered_pair(current_user.id, finded_user.id)
    
    finded_friendship = (
        db.query(Friendship)
        .filter(Friendship.user1 == min_user,
                Friendship.user2 == max_user,
                Friendship.initiator == finded_user.id,
                Friendship.status == "pending"
        )
        .first()
    )

    if not finded_friendship:
        raise HTTPException(status_code=400, detail="Cannot find that friendship")

    finded_friendship.status = "accepted"
    db.commit()

    return {"message": "Friendship was created successful"}

@router.delete("/decline_request")
def decline_request(payload: FriendRequest, current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    finded_user = db.query(User).filter(User.username == payload.target_login).first()
    
    if not finded_user:
        raise HTTPException(status_code=400, detail="Cannot find that username")

    min_user, max_user = get_ordered_pair(current_user.id, finded_user.id)
    
    finded_friendship = db.query(Friendship).filter(
        Friendship.user1 == min_user, Friendship.user2 == max_user, Friendship.status == "pending"
    ).first()

    if not finded_friendship:
        raise HTTPException(status_code=400, detail="Cannot find that friendship")

    db.delete(finded_friendship)
    db.commit()

    return {"message": "friendship was declined successful"}

@router.delete("/remove_friend")
def remove_friend(payload: FriendRequest, current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    finded_user = db.query(User).filter(User.username == payload.target_login).first()
    
    if not finded_user:
        raise HTTPException(status_code=400, detail="Cannot find that username")

    min_user, max_user = get_ordered_pair(current_user.id, finded_user.id)
    
    finded_friendship = db.query(Friendship).filter(
        Friendship.user1 == min_user, Friendship.user2 == max_user, Friendship.status == "accepted"
    ).first()

    if not finded_friendship:
        raise HTTPException(status_code=400, detail="Cannot find that friendship")

    db.delete(finded_friendship)
    db.commit()

    return {"message": "friend removed successful"}

@router.get("/incoming_requests", response_model=list[FriendRequestOut])
def get_incoming_requests(current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user1 == current_user.id,
            Friendship.user2 == current_user.id,
        ),
        Friendship.status == "pending",
        Friendship.initiator != current_user.id
    ).all()

    result = []
    for f in friendships:
        other_id = f.user2 if f.user1 == current_user.id else f.user1
        other_user = db.query(User).filter(User.id == other_id).first()
        if other_user:
            result.append(
                FriendRequestOut(
                    user=other_user,
                    created_at=f.created_at
                )
            )
    
    return result

@router.get("/outgoing_requests", response_model=list[FriendRequestOut])
def get_outgoing_requests(current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user1 == current_user.id,
            Friendship.user2 == current_user.id,
        ),
        Friendship.status == "pending",
        Friendship.initiator == current_user.id
    ).all()

    result = []
    for f in friendships:
        other_id = f.user2 if f.user1 == current_user.id else f.user1
        other_user = db.query(User).filter(User.id == other_id).first()
        if other_user:
            result.append(
                FriendRequestOut(
                    user=other_user,
                    created_at=f.created_at
                )
            )
    
    return result

@router.get("/list", response_model=list[FriendOut])
def get_friend_list(current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user1 == current_user.id,
            Friendship.user2 == current_user.id,
        ),
        Friendship.status == "accepted"
    ).all()

    friend_ids = [f.user2 if f.user1 == current_user.id else f.user1 for f in friendships]

    friends = db.query(User).filter(User.id.in_(friend_ids)).all()
    return friends