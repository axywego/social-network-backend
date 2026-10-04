import uuid
from datetime import datetime

from app.database.base import Base
from sqlalchemy import UUID, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column


class BannedUser(Base):
    __tablename__ = "banned_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    ban_reason_id: Mapped[uuid.UUID] = mapped_column(
        Integer, ForeignKey("ban_reasons.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
