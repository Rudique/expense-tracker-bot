from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.category_service import CategoryService

router = Router()

USAGE = "Использование: /add_category [emoji] [название]\nПример: /add_category 🍕 Еда"


@router.message(Command("add_category"))
async def cmd_add_category(
    message: Message,
    command: CommandObject,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not command.args:
        await message.answer(USAGE)
        return

    parts = command.args.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(USAGE)
        return

    emoji, name = parts

    async with session_factory() as session:
        category = await CategoryService.create(session=session, emoji=emoji, name=name)

    await message.answer(f"Категория добавлена: {category.emoji} {category.name}")
