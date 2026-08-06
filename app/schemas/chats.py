from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

class ChatCreate(BaseModel):
    type: Literal["direct", "group"]
    user_if_direct: Optional[UUID] = None
    name: Optional[str] = None

class ChatPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None

class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sender_id: Optional[UUID] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime

class Chat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    messages = List[Message] = []

class MessageCreate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.text and not self.image_url:
            raise ValueError("content or image_url is required")
        return self