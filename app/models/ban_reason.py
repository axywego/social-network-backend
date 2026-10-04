import uuid

from app.database.base import Base
from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column


class BanReason(Base):
    __tablename__ = "ban_reasons"

    id: Mapped[uuid.UUID] = mapped_column(Integer, primary_key=True, autoincrement=True)

    note: Mapped[str] = mapped_column(Text)
