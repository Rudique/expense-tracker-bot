import asyncio

from app.bot import create_bot, create_dispatcher, set_bot_commands
from app.config import get_settings
from app.db.session import create_engine, create_session_factory
from app.handlers import register_handlers
from app.scheduler import load_all_reminders, scheduler


async def main() -> None:
    settings = get_settings()

    engine = create_engine(settings.db_url)
    session_factory = create_session_factory(engine)

    bot = create_bot(settings.bot_token)
    dp = create_dispatcher()
    register_handlers(dp)

    await set_bot_commands(bot)

    scheduler.start()
    await load_all_reminders(bot, session_factory)

    try:
        await dp.start_polling(bot, session_factory=session_factory)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())