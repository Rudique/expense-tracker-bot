from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IntIdPkMixin, TimestampMixin


class Reminder(IntIdPkMixin, TimestampMixin, Base):
    __tablename__ = "reminders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False)   # daily|weekly|monthly|once
    schedule_value: Mapped[str | None] = mapped_column(String(20), nullable=True)  # weekday/day/date
    send_time: Mapped[str] = mapped_column(String(5), nullable=False)         # "HH:MM"
    target: Mapped[str] = mapped_column(String(20), nullable=False)           # private|group_topic
    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    thread_id: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
