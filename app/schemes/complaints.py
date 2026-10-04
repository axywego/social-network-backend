import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComplaintCreate(BaseModel):
    reported_id: uuid.UUID
    reported_by_reason: int


class ComplaintOut(BaseModel):
    sender_username: str
    reported_username: str
    reported_at: datetime

    model_config = ConfigDict(from_attributes=True)
