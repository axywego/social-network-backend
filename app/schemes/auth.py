from datetime import date

from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    patronymic: str | None = None
    birthday: date | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str
