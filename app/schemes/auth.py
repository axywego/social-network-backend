from datetime import date

from app.schemes.users import validate_birthday
from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    username: str = Field(..., min_length=5, max_length=32)
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)
    patronymic: str | None = Field(None, max_length=30)
    birthday: date | None = None

    @field_validator("birthday")
    @classmethod
    def _check_birthday(cls, value: date | None) -> date | None:
        return validate_birthday(value)


class UserLogin(BaseModel):
    username: str = Field(..., max_length=32)
    password: str = Field(..., max_length=128)


class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str
