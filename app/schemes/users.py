from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserChange(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)
    patronymic: str | None = Field(None, max_length=30)
    bio: str | None = Field(None, max_length=200)
    birthday: date | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    first_name: str
    last_name: str
    patronymic: str | None = None
    bio: str | None = None
    birthday: date | None = None
    avatar_url: str | None = None


class PaginatedUsers(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[UserOut]
    total: int
    limit: int
    offset: int
