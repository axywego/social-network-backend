from sqlalchemy import Column, BigInteger, Identity, Text, DateTime, ForeignKey, CheckConstraint, Index, desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class ChatMessage(Base):
    __tablename__ = "chat_message"

    id = Column(BigInteger, Identity(), primary_key=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    content = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("content is not null or image is not null", name="check_content_or_image"),
        Index("idx_chat_message_chat_id_created_at", "chat_id", desc("created_at")),
    )