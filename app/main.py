import asyncio

import structlog

from app.bot import create_bot, create_dispatcher, set_bot_commands
from app.config import get_settings
from app.db.session import create_engine, create_session_factory
from app.handlers import register_handlers
from app.logging_config import setup_logging
from app.middleware.logging import LoggingMiddleware
from app.scheduler import load_all_reminders, scheduler

logger = structlog.get_logger()


async def main() -> None:
    settings = get_settings()
    setup_logging(level=settings.log_level, fmt=settings.log_format)

    logger.info("bot_starting", db_url=settings.db_url.split("@")[-1])

    engine = create_engine(settings.db_url)
    session_factory = create_session_factory(engine)

    bot = create_bot(settings.bot_token)
    dp = create_dispatcher()
    register_handlers(dp)

    dp.message.outer_middleware(LoggingMiddleware())
    dp.callback_query.outer_middleware(LoggingMiddleware())

    await set_bot_commands(bot)

    scheduler.start()
    reminders = await load_all_reminders(bot, session_factory)

    logger.info("bot_started", reminders_loaded=reminders)

    try:
        await dp.start_polling(bot, session_factory=session_factory)
    finally:
        scheduler.shutdown()
        logger.info("bot_stopped")


if __name__ == "__main__":
    asyncio.run(main())