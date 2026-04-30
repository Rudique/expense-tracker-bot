from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand


def create_bot(token: str) -> Bot:
    return Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    return Dispatcher()


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start",           description="Start the bot"),
        BotCommand(command="add_transaction", description="Add a new transaction"),
        BotCommand(command="my_stats",        description="View your spending by period"),
        BotCommand(command="categories",      description="View all categories"),
        BotCommand(command="add_category",    description="Add a new category"),
        BotCommand(command="group_stats",     description="View spending for all users"),
        BotCommand(command="add_reminder",        description="Set up a reminder"),
        BotCommand(command="my_reminders",        description="Manage your reminders"),
        BotCommand(command="set_reminders_topic", description="Link this topic for reminders (run inside topic)"),
    ]
    await bot.set_my_commands(commands)