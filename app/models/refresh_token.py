import uuid
from sqlalchemy import Column, String, DateTime, BigInteger, Identity, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, Identity(), primary_key=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)