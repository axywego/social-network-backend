from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

from datetime import date
from uuid import UUID

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    first_name: str
    last_name: str
    patronymic: Optional[str]
    birthday: Optional[date]
