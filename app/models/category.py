from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IntIdPkMixin, TimestampMixin


class Category(IntIdPkMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emoji: Mapped[str | None] = mapped_column(String(255), nullable=True)
