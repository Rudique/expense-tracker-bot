from datetime import datetime

import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = structlog.get_logger()

from app.fsm.stats import GroupPeriodCallback, PeriodCallback
from app.keyboards.stats import back_to_periods_kb, group_back_to_periods_kb, group_period_kb, period_kb
from app.services.stats_service import PERIOD_FUNCTIONS, PERIOD_LABELS, StatsService
from app.services.user_service import UserService
from app.texts.stats import group_stats_text, stats_text

router = Router()


# ── /my_stats ──────────────────────────────────────────────────────────────────

@router.message(Command("my_stats"))
async def cmd_my_stats(message: Message) -> None:
    await message.answer("📊 <b>Select period:</b>", reply_markup=period_kb())


@router.callback_query(PeriodCallback.filter())
async def on_period(
    callback: CallbackQuery,
    callback_data: PeriodCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    period = callback_data.period

    if period == "back":
        await callback.message.edit_text("📊 <b>Select period:</b>", reply_markup=period_kb())
        return

    date_from, date_to = PERIOD_FUNCTIONS[period]()

    async with session_factory() as session:
        user = await UserService.get_or_create(session, callback.from_user)
        rows = await StatsService.get_by_period(
            session=session,
            user_id=user.id,
            date_from=date_from,
            date_to=date_to,
        )

    logger.info("stats_viewed", period=period, rows=len(rows))
    await callback.message.edit_text(
        stats_text(PERIOD_LABELS[period], rows, date_from, date_to),
        reply_markup=back_to_periods_kb(),
    )


# ── /group_stats ───────────────────────────────────────────────────────────────

@router.message(Command("group_stats"))
async def cmd_group_stats(message: Message) -> None:
    await message.answer("👥 <b>Select period:</b>", reply_markup=group_period_kb())


@router.callback_query(GroupPeriodCallback.filter())
async def on_group_period(
    callback: CallbackQuery,
    callback_data: GroupPeriodCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    period = callback_data.period

    if period == "back":
        await callback.message.edit_text("👥 <b>Select period:</b>", reply_markup=group_period_kb())
        return

    date_from, date_to = PERIOD_FUNCTIONS[period]()

    async with session_factory() as session:
        rows = await StatsService.get_all_by_period(
            session=session,
            date_from=date_from,
            date_to=date_to,
        )

    logger.info("group_stats_viewed", period=period, rows=len(rows))
    await callback.message.edit_text(
        group_stats_text(PERIOD_LABELS[period], rows, date_from, date_to),
        reply_markup=group_back_to_periods_kb(),
    )
