from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.user_service import UserService

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tg_user = message.from_user

    print(tg_user)

    if tg_user is None:
        await message.answer("не удалось получить данные пользователя")
        return

    async with session_factory() as session:
        user, created = await UserService.create_or_update_from_telegram(
            session=session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )

    if created:
        await message.answer(f"привет, {user.first_name or 'user'}! ты добавлен в базу")
    else:
        await message.answer(f"с возвращением, {user.first_name or 'user'}!!!")