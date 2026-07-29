from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class UserRegister(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    patronymic: Optional[str]
    birthday: Optional[date]

class UserLogin(BaseModel):
    username: str
    password: str

class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class RefreshRequest(BaseModel):
    refresh_token: str