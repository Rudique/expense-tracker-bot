import asyncio

from app.bot import create_bot, create_dispatcher
from app.config import get_settings
from app.db.init_db import init_db
from app.db.session import create_engine, create_session_factory
from app.handlers import register_handlers


async def main() -> None:
    settings = get_settings()

    engine = create_engine(settings.db_url)
    session_factory = create_session_factory(engine)

    # пока просто создаем, позже будем прокидывать в handlers/middlewares
    _ = session_factory

    await init_db(engine)

    bot = create_bot(settings.bot_token)
    dp = create_dispatcher()
    register_handlers(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())