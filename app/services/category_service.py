from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryService:
    @staticmethod
    async def create(session: AsyncSession, emoji: str, name: str) -> Category:
        category = Category(emoji=emoji, name=name)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category
