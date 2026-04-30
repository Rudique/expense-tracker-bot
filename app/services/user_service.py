from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserService:
    @staticmethod
    async def get_or_create(session: AsyncSession, tg_user: TgUser) -> User:
        user, _ = await UserService.create_or_update_from_telegram(
            session=session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        return user

    @staticmethod
    async def create_or_update_from_telegram(
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> tuple[User, bool]:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        created = False

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            created = True
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name

        await session.commit()
        await session.refresh(user)

        return user, created