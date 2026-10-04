from app.core.dependencies import get_current_user
from app.database.session_db import get_db
from app.models import ban_reason
from app.models.ban_reason import BanReason
from app.models.complaint import Complaint
from app.models.user import User
from app.schemes.complaints import ComplaintCreate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reported = db.get(User, payload.reported_id)
    if not reported:
        raise HTTPException(status_code=404, detail="User not found")

    reason = db.get(BanReason, payload.reported_by_reason)
    if not reason:
        raise HTTPException(status_code=404, detail="Reason not found")

    complaint = Complaint(
        user_id=reported.id, ban_reason_id=reason.id, sender_id=current_user.id
    )
    db.add(complaint)
    db.commit()

    return {"message": "Complaint successfuly sended"}
