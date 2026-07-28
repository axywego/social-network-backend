from pydantic import BaseModel, EmailStr, ConfigDict, Field, Optional
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
