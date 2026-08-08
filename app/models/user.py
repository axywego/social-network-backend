from sqlalchemy import Column, String, Text, DateTime, Date, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    username = Column(String(32), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)

    first_name = Column(String(30), nullable=False)
    last_name = Column(String(30), nullable=False)
    patronymic = Column(String(30))
    bio = Column(String(200))
    birthday = Column(Date)
    avatar_url = Column(String)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())