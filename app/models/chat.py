from sqlalchemy import Column, Text, DateTime, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    type = Column(Text, nullable=False)

    name = Column(Text, nullable=True)

    user_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user_b_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("type in ('direct', 'group')", name="check_type_valid"),
        CheckConstraint("""
            (type = 'direct' and user_a_id is not null and user_b_id is not null and user_a_id < user_b_id and name is null)
            or
            (type = 'group' and user_a_id is null and user_b_id is null and name is not null)""",
            name="check_valid_table_variables"),
        Index(
            "idx_unique_direct_chat",
            "user_a_id", "user_b_id",
            unique=True,
            postgresql_where=text("type = 'direct'"),
        ),
    )