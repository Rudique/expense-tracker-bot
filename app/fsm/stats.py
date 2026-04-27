from aiogram.filters.callback_data import CallbackData


class PeriodCallback(CallbackData, prefix="stats_p"):
    period: str  # today | week | last_7 | last_30 | month | last_month | last_3months | this_year | back


class GroupPeriodCallback(CallbackData, prefix="stats_gp"):
    period: str  # same values as PeriodCallback
