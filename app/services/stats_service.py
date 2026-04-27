from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User


@dataclass
class CategoryStats:
    emoji: str
    name: str
    total: Decimal
    count: int
    is_shared: bool


@dataclass
class UserCategoryStats:
    user_id: int
    username: str | None
    first_name: str | None
    emoji: str
    name: str
    total: Decimal
    count: int
    is_shared: bool


# ── Period helpers ─────────────────────────────────────────────────────────────

def period_today() -> tuple[datetime, datetime]:
    now = datetime.now()
    return (
        now.replace(hour=0, minute=0, second=0, microsecond=0),
        now.replace(hour=23, minute=59, second=59, microsecond=999999),
    )


def period_this_week() -> tuple[datetime, datetime]:
    now = datetime.now()
    start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return start, now


def period_this_month() -> tuple[datetime, datetime]:
    now = datetime.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now


def period_last_month() -> tuple[datetime, datetime]:
    now = datetime.now()
    first_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = first_this - timedelta(microseconds=1)
    start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, end


def period_last_7_days() -> tuple[datetime, datetime]:
    now = datetime.now()
    return now - timedelta(days=7), now


def period_last_30_days() -> tuple[datetime, datetime]:
    now = datetime.now()
    return now - timedelta(days=30), now


def period_last_3_months() -> tuple[datetime, datetime]:
    now = datetime.now()
    return now - timedelta(days=90), now


def period_this_year() -> tuple[datetime, datetime]:
    now = datetime.now()
    return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0), now


PERIOD_FUNCTIONS = {
    "today":        period_today,
    "week":         period_this_week,
    "last_7":       period_last_7_days,
    "last_30":      period_last_30_days,
    "month":        period_this_month,
    "last_month":   period_last_month,
    "last_3months": period_last_3_months,
    "this_year":    period_this_year,
}

PERIOD_LABELS = {
    "today":        "Today",
    "week":         "This week",
    "last_7":       "Last 7 days",
    "last_30":      "Last 30 days",
    "month":        "This month",
    "last_month":   "Last month",
    "last_3months": "Last 3 months",
    "this_year":    "This year",
}


# ── Service ────────────────────────────────────────────────────────────────────

class StatsService:
    @staticmethod
    async def get_by_period(
        session: AsyncSession,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> list[CategoryStats]:
        result = await session.execute(
            select(
                Category.emoji,
                Category.name,
                Transaction.is_shared,
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("count"),
            )
            .join(Category, Transaction.category_id == Category.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.created_at >= date_from,
                Transaction.created_at < date_to,
            )
            .group_by(Category.id, Category.emoji, Category.name, Transaction.is_shared)
            .order_by(Transaction.is_shared, func.sum(Transaction.amount).desc())
        )
        return [
            CategoryStats(
                emoji=row.emoji,
                name=row.name,
                total=row.total,
                count=row.count,
                is_shared=row.is_shared,
            )
            for row in result.all()
        ]

    @staticmethod
    async def get_all_by_period(
        session: AsyncSession,
        date_from: datetime,
        date_to: datetime,
    ) -> list[UserCategoryStats]:
        result = await session.execute(
            select(
                User.id.label("user_id"),
                User.username,
                User.first_name,
                Category.emoji,
                Category.name,
                Transaction.is_shared,
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("count"),
            )
            .join(Category, Transaction.category_id == Category.id)
            .join(User, Transaction.user_id == User.id)
            .where(
                Transaction.created_at >= date_from,
                Transaction.created_at < date_to,
            )
            .group_by(
                User.id, User.username, User.first_name,
                Category.id, Category.emoji, Category.name,
                Transaction.is_shared,
            )
            .order_by(Transaction.is_shared, User.id, func.sum(Transaction.amount).desc())
        )
        return [
            UserCategoryStats(
                user_id=row.user_id,
                username=row.username,
                first_name=row.first_name,
                emoji=row.emoji,
                name=row.name,
                total=row.total,
                count=row.count,
                is_shared=row.is_shared,
            )
            for row in result.all()
        ]
