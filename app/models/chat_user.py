import uuid
from sqlalchemy import Column, BigInteger, Identity, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base


class ChatUser(Base):
    __tablename__ = "chat_user"

    id = Column(BigInteger, Identity(), primary_key=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_chat_user_chat_id_user_id"),
        Index("idx_chat_user_user_id", "user_id"),
        Index("idx_chat_user_chat_id", "chat_id"),
    )