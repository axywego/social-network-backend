import uuid
from sqlalchemy import Column, Text, DateTime, BigInteger, Identity, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(BigInteger, Identity(), primary_key=True)
    user1 = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user2 = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    initiator = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    status = Column(Text, nullable=False, server_default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status in ('pending', 'accepted')", name ="check_status_valid"),
        CheckConstraint("user1 < user2", name="check_users_order"),
        UniqueConstraint("user1, user2", name="unique_friendship"),

        Index("idx_friendships_user2", "user2")
    )