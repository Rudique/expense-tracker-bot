from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("add_transaction"))
async def cmd_add_transaction(message: Message) -> None:
    await message.answer("🚧 <b>Under construction</b>\n\nThis feature is coming soon!")
