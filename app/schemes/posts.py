from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import model_validator


class PostCommentCreate(BaseModel):
    post_id: int
    content: str = Field(..., min_length=1, max_length=2000)


class PostCreate(BaseModel):
    content: str | None = Field(None, max_length=5000)
    image_url: str | None = None

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.content and not self.image_url:
            raise ValueError("content or image_url is required")
        return self


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
    content: str | None = Field(None, max_length=5000)
    image_url: str | None = None

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.content and not self.image_url:
            raise ValueError("content or image_url is required")
        return self


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
