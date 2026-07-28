from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session_db import get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()