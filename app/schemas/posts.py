from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List

from datetime import date, datetime
from uuid import UUID

class PostCommentCreate(BaseModel):
    post_id: int

    content: Optional[str] = None

class PostCreate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None

class PostCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID

    content: Optional[str] = None

    created_at: datetime

class PostAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str

    avatar_url: str

class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: int

    author: PostAuthor

    content: Optional[str] = None
    image_url: Optional[str] = None

    created_at: datetime

    comments: List[PostCommentOut] = Field(default_factory=list)
    likes: int

    liked_by_me: bool = False