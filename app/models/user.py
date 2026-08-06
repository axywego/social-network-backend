import uuid
from sqlalchemy import Column, String, DateTime, VARCHAR, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    username = Column(VARCHAR(32), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    first_name = Column(VARCHAR(30), nullable=False)
    last_name = Column(VARCHAR(30), nullable=False)
    patronymic = Column(VARCHAR(30))
    birthday = Column(Date)
    avatar_url = Column(String)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())