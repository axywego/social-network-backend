from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FriendRequest(BaseModel):
    target_login: str = Field(..., max_length=32)


class FriendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    first_name: str
    last_name: str
    avatar_url: str | None = None


class FriendRequestOut(BaseModel):
    user: FriendOut
    created_at: datetime
