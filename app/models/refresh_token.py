import uuid
from sqlalchemy import Column, Text, DateTime, BigInteger, Identity, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, Identity(), primary_key=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id")
    )