from pydantic import BaseModel, EmailStr, ConfigDict, Field
from uuid import UUID

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    password_hash: str