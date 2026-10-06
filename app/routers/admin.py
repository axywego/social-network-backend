import asyncio
import uuid

from app.core.dependencies import get_current_admin
from app.database.session_db import get_db
from app.models.ban_reason import BanReason
from app.models.banned_user import BannedUser
from app.models.complaint import Complaint
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemes.complaints import ComplaintOut
from app.schemes.users import UserOut
from app.ws.manager import manager
from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, aliased

router = APIRouter(prefix="/admin", tags=["admin"])


def _revoke_sessions(db: Session, user_id: uuid.UUID) -> None:
    """Drop refresh tokens so no device can mint a new access token."""
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))


def _push_ban_event(user: User, db: Session) -> None:
    """Kick the user off live sockets; a banned client gets 403 anyway."""
    reason = None
    if user.banned_reason is not None:
        found = db.get(BanReason, user.banned_reason)
        reason = found.note if found else None

    message = {"type": "banned", "reason": reason}
    try:
        # The endpoint is sync, so the publish goes to the running loop.
        loop = asyncio.get_running_loop()
        loop.create_task(manager.send_to_user(str(user.id), message))
    except RuntimeError:
        pass


@router.post("/complaints/{complaint_id}", dependencies=[(Depends(get_current_admin))])
def approve_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    reported = db.get(User, complaint.user_id)
    if not reported:
        raise HTTPException(status_code=404, detail="Reported user not found")

    already_banned = db.execute(
        select(BannedUser).where(BannedUser.user_id == complaint.user_id)
    ).scalar_one_or_none()

    if not already_banned:
        db.add(
            BannedUser(user_id=complaint.user_id, ban_reason_id=complaint.ban_reason_id)
        )

    reported.is_banned = True
    reported.banned_reason = complaint.ban_reason_id
    _revoke_sessions(db, reported.id)

    db.delete(complaint)
    db.commit()

    _push_ban_event(reported, db)

    return {"message": "complaint approved successful"}


@router.delete(
    "/complaints/{complaint_id}", dependencies=[(Depends(get_current_admin))]
)
def decline_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    db.delete(complaint)
    db.commit()

    return {"message": "complaint declined successful"}


@router.get(
    "/complaints",
    response_model=Page[ComplaintOut],
    dependencies=[(Depends(get_current_admin))],
)
def get_complaints(db: Session = Depends(get_db), params: Params = Depends()):
    Sender = aliased(User)
    Reported = aliased(User)
    return paginate(
        db,
        select(
            Complaint.id,
            Sender.username.label("sender_username"),
            Reported.username.label("reported_username"),
            Reported.id.label("reported_id"),
            BanReason.note.label("ban_reason"),
            Complaint.created_at.label("reported_at"),
        )
        .join(Sender, Sender.id == Complaint.sender_id)
        .join(Reported, Reported.id == Complaint.user_id)
        .join(BanReason, BanReason.id == Complaint.ban_reason_id)
        .order_by(Complaint.created_at.asc()),
        params,
    )


@router.get(
    "/banned", response_model=Page[UserOut], dependencies=[(Depends(get_current_admin))]
)
def get_banned_users(db: Session = Depends(get_db), params: Params = Depends()):
    return paginate(
        db,
        select(User)
        .join(BannedUser, BannedUser.user_id == User.id)
        .order_by(User.username),
        params,
    )


@router.delete("/banned/{user_id}", dependencies=[(Depends(get_current_admin))])
def unban_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ban = db.execute(
        select(BannedUser).where(BannedUser.user_id == user_id)
    ).scalar_one_or_none()
    if not ban:
        raise HTTPException(status_code=404, detail="User is not banned")

    db.delete(ban)
    user.is_banned = False
    user.banned_reason = None
    db.commit()

    return {"message": "user unbanned successful"}


@router.get(
    "/users", response_model=Page[UserOut], dependencies=[(Depends(get_current_admin))]
)
def get_users(db: Session = Depends(get_db), params: Params = Depends()):
    return paginate(db, select(User).order_by(User.username), params)
