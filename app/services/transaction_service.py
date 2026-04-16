from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction


class TransactionService:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        category_id: int,
        comment: str | None,
        is_shared: bool = False,
    ) -> Transaction:
        try:
            transaction = Transaction(user_id=user_id, amount=amount, category_id=category_id, comment=comment, is_shared=is_shared)
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            return transaction
        except Exception:
            await session.rollback()
            raise
