from app.core.dependencies import get_current_user
from app.database.session_db import get_db
from app.models.ban_reason import BanReason
from app.models.complaint import Complaint
from app.models.user import User
from app.schemes.complaints import BanReasonOut, ComplaintCreate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.get("/reasons", response_model=list[BanReasonOut])
def get_reasons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.execute(select(BanReason).order_by(BanReason.id)).scalars().all()


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.reported_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Нельзя пожаловаться на самого себя"
        )

    reported = db.get(User, payload.reported_id)
    if not reported:
        raise HTTPException(status_code=404, detail="User not found")

    reason = db.get(BanReason, payload.reported_by_reason)
    if not reason:
        raise HTTPException(status_code=404, detail="Reason not found")

    # One open complaint per (sender, reported) pair keeps the admin
    # queue free of stacked copies of the same report.
    already_exists = db.execute(
        select(Complaint).where(
            Complaint.sender_id == current_user.id,
            Complaint.user_id == reported.id,
        )
    ).scalar_one_or_none()
    if already_exists:
        raise HTTPException(
            status_code=409, detail="Вы уже пожаловались на этого пользователя"
        )

    complaint = Complaint(
        user_id=reported.id, ban_reason_id=reason.id, sender_id=current_user.id
    )
    db.add(complaint)
    db.commit()

    return {"message": "Complaint successfuly sended"}
