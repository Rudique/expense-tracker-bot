from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer("HI! IM EXPENSE TRACKER BOT! I CAN HELP YOU TO TRACK YOUR EXPENSES AND INCOME. USE /help TO SEE ALL COMMANDS.")