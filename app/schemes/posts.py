from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PostCommentCreate(BaseModel):
    post_id: int

    content: str


class PostCreate(BaseModel):
    content: str | None = None
    image_url: str | None = None


class PostCommentAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    avatar_url: str | None = None


class PostCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    author: PostCommentAuthor
    content: str
    created_at: datetime


class PostAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    avatar_url: str | None = None


class PostUpdate(BaseModel):
    content: str | None = None
    image_url: str | None = None


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    author: PostAuthor

    content: str | None = None
    image_url: str | None = None

    created_at: datetime

    comments: list[PostCommentOut] = Field(default_factory=list)

    likes: int
    liked_by_me: bool = False
