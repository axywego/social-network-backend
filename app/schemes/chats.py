from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

class ChatCreate(BaseModel):
    type: Literal["direct", "group"]
    user_if_direct: Optional[UUID] = None
    name: Optional[str] = None

    @model_validator(mode="after")
    def validate_fields(self):
        if self.type == "direct":
            if self.user_if_direct is None:
                raise ValueError("user_if_direct if required for direct chats")
        if self.type == "group":
            if not self.name:
                raise ValueError("name is required for group chats")
        return self

class ChatPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chat_id: UUID
    type: Literal["direct", "group"]
    name: str
    unread_count: int
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    avatar_url: Optional[str] = None

class AddRemoveUserFromChat(BaseModel):
    chat_id: UUID
    user_id: UUID

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: Optional[UUID] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    created_at: datetime

class Chat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chat_id: UUID
    messages: List[MessageOut] = []

class MessageCreate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.content and not self.image_url:
            raise ValueError("content or image_url is required")
        return self