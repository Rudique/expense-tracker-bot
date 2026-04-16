from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.category_service import CategoryService

router = Router()

USAGE = (
    "📋 <b>Add a new category</b>\n\n"
    "Usage: /add_category [emoji] [name]\n"
    "Example: /add_category 🍕 Fast Food"
)


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

    await message.answer(
        f"✅ Category added!\n\n"
        f"{category.emoji} <b>{category.name}</b>"
    )


@router.message(Command("categories"))
async def cmd_categories(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        categories = await CategoryService.get_all(session=session)

    if not categories:
        await message.answer("📭 No categories yet.\n\nAdd one with /add_category")
        return

    lines = "\n".join(f"{c.emoji} {c.name}" for c in categories)
    await message.answer(f"📋 <b>Your categories</b>\n\n{lines}")
