from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session_db import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])
