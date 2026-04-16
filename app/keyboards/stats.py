from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.fsm.stats import PeriodCallback


def period_kb() -> InlineKeyboardMarkup:
    def btn(text: str, period: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=PeriodCallback(period=period).pack())

    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("📅 Today",        "today"),      btn("📅 This week",    "week")],
        [btn("📅 Last 7 days",  "last_7"),     btn("📅 Last 30 days", "last_30")],
        [btn("📅 This month",   "month"),      btn("📅 Last month",   "last_month")],
        [btn("📅 Last 3 months","last_3months"),btn("📅 This year",   "this_year")],
    ])


def back_to_periods_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Change period", callback_data=PeriodCallback(period="back").pack()),
    ]])
