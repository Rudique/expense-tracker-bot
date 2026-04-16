from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.transaction import Transaction
from app.services.transaction_service import TransactionService


async def save_transaction(
    session_factory: async_sessionmaker[AsyncSession],
    data: dict,
    comment: Optional[str],
) -> Transaction:
    async with session_factory() as session:
        transaction = await TransactionService.create(
            session=session,
            user_id=data["user_id"],
            amount=Decimal(data["amount"]),
            category_id=data["category_id"],
            comment=comment,
            is_shared=data["is_shared"],
        )
    return transaction
