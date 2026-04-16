from aiogram.filters.callback_data import CallbackData


class PeriodCallback(CallbackData, prefix="stats_p"):
    period: str  # today | week | last_7 | last_30 | month | last_month | last_3months | this_year | back
