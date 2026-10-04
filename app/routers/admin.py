import uuid

from app.core.dependencies import get_current_admin
from app.database.session_db import get_db
from app.models.banned_user import BannedUser
from app.models.complaint import Complaint
from app.models.user import User
from app.schemes.complaints import ComplaintOut
from app.schemes.users import UserOut
from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/complaints/{complaint_id}", dependencies=[(Depends(get_current_admin))])
def approve_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    banned_user = BannedUser(
        user_id=complaint.user_id,
        ban_reason_id=complaint.ban_reason_id,
    )
    db.add(banned_user)
    db.delete(complaint)

    db.commit()

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
def get_complaints(db: Session = Depends(get_db)):
    Sender = aliased(User)
    Reported = aliased(User)
    return paginate(
        db,
        select(
            User.username.label("sender_username"),
            User.username.label("report_username"),
            Complaint.created_at.label("reported_at"),
        )
        .join(Sender, Sender.id == Complaint.sender_id)
        .join(Reported, Reported.id == Complaint.user_id)
        .order_by(Complaint.created_at.asc()),
    )


@router.get(
    "/banned", response_model=Page[UserOut], dependencies=[(Depends(get_current_admin))]
)
def get_banned_users(db: Session = Depends(get_db)):
    return paginate(db, select(User).join(BannedUser, BannedUser.user_id == User.id))


@router.get(
    "/users", response_model=Page[UserOut], dependencies=[(Depends(get_current_admin))]
)
def get_users(db: Session = Depends(get_db)):
    return paginate(db, select(User).order_by(User.username))
