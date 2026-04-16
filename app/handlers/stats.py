from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.fsm.stats import PeriodCallback
from app.keyboards.stats import back_to_periods_kb, period_kb
from app.services.stats_service import PERIOD_FUNCTIONS, PERIOD_LABELS, StatsService
from app.services.user_service import UserService
from app.texts.stats import stats_text

router = Router()


async def _resolve_user_id(
    from_user,
    session_factory: async_sessionmaker[AsyncSession],
) -> int:
    async with session_factory() as session:
        user, _ = await UserService.create_or_update_from_telegram(
            session=session,
            telegram_id=from_user.id,
            username=from_user.username,
            first_name=from_user.first_name,
            last_name=from_user.last_name,
        )
    return user.id


async def _show_stats(
    target,          # Message or CallbackQuery.message to edit
    user_id: int,
    session_factory: async_sessionmaker[AsyncSession],
    period_label: str,
    date_from: datetime,
    date_to: datetime,
    edit: bool = True,
) -> None:
    async with session_factory() as session:
        rows = await StatsService.get_by_period(
            session=session,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )
    text = stats_text(period_label, rows)
    if edit:
        await target.edit_text(text, reply_markup=back_to_periods_kb())
    else:
        await target.answer(text, reply_markup=back_to_periods_kb())


# ── Handlers ───────────────────────────────────────────────────────────────────

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
    user_id = await _resolve_user_id(callback.from_user, session_factory)
    await _show_stats(
        callback.message, user_id, session_factory,
        period_label=PERIOD_LABELS[period],
        date_from=date_from,
        date_to=date_to,
    )


