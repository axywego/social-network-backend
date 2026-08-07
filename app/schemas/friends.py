from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class FriendRequest(BaseModel):
    target_login: str

class FriendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    birthday: Optional[date] = None

class FriendRequestOut(BaseModel):
    user: FriendOut
    created_at: datetime