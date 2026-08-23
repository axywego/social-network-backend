import uuid
from datetime import datetime

from app.database.base import Base
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)

    name: Mapped[str | None] = mapped_column(Text)

    user_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    user_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    avatar_url: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("type in ('direct', 'group')", name="check_type_valid"),
        CheckConstraint(
            """
            (type = 'direct' and user_a_id is not null and user_b_id is not null and user_a_id < user_b_id and name is null)
            or
            (type = 'group' and user_a_id is null and user_b_id is null and name is not null)""",
            name="check_valid_table_variables",
        ),
        Index(
            "idx_unique_direct_chat",
            "user_a_id",
            "user_b_id",
            unique=True,
            postgresql_where=text("type = 'direct'"),
        ),
    )
