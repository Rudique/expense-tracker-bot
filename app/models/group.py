from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IntIdPkMixin, TimestampMixin


class Group(IntIdPkMixin, TimestampMixin, Base):
    __tablename__ = "groups"

    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reminders_thread_id: Mapped[int | None] = mapped_column(nullable=True)
