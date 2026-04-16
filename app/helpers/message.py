from aiogram.types import InlineKeyboardMarkup, Message


async def delete_message(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        pass


async def edit_message(
    message: Message,
    msg_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg_id,
            text=text,
            reply_markup=reply_markup,
        )
        return True
    except Exception:
        return False
