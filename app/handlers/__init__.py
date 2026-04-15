from aiogram import Dispatcher

from app.handlers.start import router as start_router
from app.handlers.transaction import router as transaction_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(transaction_router)