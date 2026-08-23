from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class ChatType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"


class ChatCreate(BaseModel):
    type: ChatType
    user_if_direct: UUID | None = None
    name: str | None = None

    @model_validator(mode="after")
    def validate_fields(self):
        if self.type == ChatType.DIRECT and self.user_if_direct is None:
            raise ValueError("user_if_direct if required for direct chats")
        if self.type == ChatType.GROUP and self.name is None:
            raise ValueError("name is required for group chats")
        return self


class ChatPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chat_id: UUID
    type: ChatType
    name: str
    unread_count: int
    last_message: str | None = None
    last_message_time: datetime | None = None
    avatar_url: str | None = None


class AddRemoveUserFromChat(BaseModel):
    chat_id: UUID
    user_id: UUID


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: UUID | None = None
    content: str | None = None
    image_url: str | None = None
    image_width: int | None = None
    image_height: int | None = None
    created_at: datetime


class Chat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chat_id: UUID
    messages: list[MessageOut] = []


class MessageCreate(BaseModel):
    content: str | None = None
    image_url: str | None = None
    image_width: int | None = None
    image_height: int | None = None

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.content and not self.image_url:
            raise ValueError("content or image_url is required")
        return self
