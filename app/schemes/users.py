from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_AGE_YEARS = 120


def validate_birthday(value: date | None) -> date | None:
    if value is None:
        return None

    today = date.today()
    if value > today:
        raise ValueError("birthday не может быть в будущем")

    had_birthday = (today.month, today.day) >= (value.month, value.day)
    age = today.year - value.year - (0 if had_birthday else 1)
    if age > MAX_AGE_YEARS:
        raise ValueError(f"birthday не может быть раньше {MAX_AGE_YEARS} лет")

    return value


class UserChange(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)
    patronymic: str | None = Field(None, max_length=30)
    bio: str | None = Field(None, max_length=200)
    birthday: date | None = None

    @field_validator("birthday")
    @classmethod
    def _check_birthday(cls, value: date | None) -> date | None:
        return validate_birthday(value)


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
    role: str
    is_banned: bool


class PaginatedUsers(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[UserOut]
    total: int
    limit: int
    offset: int
