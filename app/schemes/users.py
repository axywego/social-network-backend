from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

from datetime import date
from uuid import UUID

class UserChange(BaseModel):
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    bio: Optional[str] = None
    birthday: Optional[date] = None

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    bio: Optional[str] = None
    birthday: Optional[date] = None
    avatar_url: Optional[str] = None
