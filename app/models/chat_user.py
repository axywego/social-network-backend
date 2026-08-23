import uuid
from datetime import datetime

from app.database.base import Base
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class ChatUser(Base):
    __tablename__ = "chat_user"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    last_read_message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("chat_message.id")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_chat_user_chat_id_user_id"),
        Index("idx_chat_user_user_id", "user_id"),
        Index("idx_chat_user_chat_id", "chat_id"),
        Index("idx_chat_user_last_read", "chat_id", "last_read_message_id"),
    )
