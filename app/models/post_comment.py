from sqlalchemy import Column, BigInteger, Identity, Text, DateTime, ForeignKey, CheckConstraint, Index, desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base

class Post(Base):
    __table_name__ = "post_comments"

    id = Column(BigInteger, Identity(), primary_key=True)

    post_id = Column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullabe=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullabe=False)

    content = Column(Text)
    image_url = Column(Text)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("content is not null or image_url is not null", name="check_post_data"),
        Index("idx_post_comments_post_id_created_at", "post_id", desc("created_at"))
    )