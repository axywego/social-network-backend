import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComplaintCreate(BaseModel):
    reported_id: uuid.UUID
    reported_by_reason: int


class BanReasonOut(BaseModel):
    id: int
    note: str

    model_config = ConfigDict(from_attributes=True)


class ComplaintOut(BaseModel):
    id: int
    sender_username: str
    reported_username: str
    reported_id: uuid.UUID
    ban_reason: str
    reported_at: datetime

    model_config = ConfigDict(from_attributes=True)
