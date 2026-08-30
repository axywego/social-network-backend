import uuid

from app.database.base import Base
from sqlalchemy import BigInteger, ForeignKey, Identity, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PostLike(Base):
    __tablename__ = "post_likes"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("post_id", "user_id"),
        Index("idx_post_likes_post_id", "post_id"),
    )
