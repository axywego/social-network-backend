from sqlalchemy import Column, BigInteger, Identity, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base

class Post(Base):
    __table_name__ = "post_comments"

    id = Column(BigInteger, Identity(), primary_key=True)

    post_id = Column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullabe=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullabe=False)

    __table_args__ = (
        UniqueConstraint("post_id, user_id"),
        Index("idx_post_likes_post_id", "post_id")
    )