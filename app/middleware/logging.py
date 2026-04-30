from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from structlog.contextvars import bind_contextvars, clear_contextvars

logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        clear_contextvars()

        user = getattr(event, "from_user", None)
        if user:
            bind_contextvars(
                user_id=user.id,
                username=user.username,
            )

        if isinstance(event, Message):
            logger.info(
                "message",
                text=event.text,
                chat_id=event.chat.id,
                chat_type=event.chat.type,
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                "callback",
                data=event.data,
                chat_id=event.message.chat.id if event.message else None,
            )

        try:
            return await handler(event, data)
        except Exception:
            logger.exception("handler_error")
            raise
