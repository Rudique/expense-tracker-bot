from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.fsm.stats import GroupPeriodCallback, PeriodCallback

_PERIOD_ROWS = [
    [("📅 Today", "today"),         ("📅 This week",    "week")],
    [("📅 Last 7 days", "last_7"),  ("📅 Last 30 days", "last_30")],
    [("📅 This month", "month"),    ("📅 Last month",   "last_month")],
    [("📅 Last 3 months", "last_3months"), ("📅 This year", "this_year")],
]


def period_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=PeriodCallback(period=p).pack()) for t, p in row]
        for row in _PERIOD_ROWS
    ])


def back_to_periods_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Change period", callback_data=PeriodCallback(period="back").pack()),
    ]])


def group_period_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=GroupPeriodCallback(period=p).pack()) for t, p in row]
        for row in _PERIOD_ROWS
    ])


def group_back_to_periods_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Change period", callback_data=GroupPeriodCallback(period="back").pack()),
    ]])
