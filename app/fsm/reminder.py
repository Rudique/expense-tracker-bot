from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class AddReminder(StatesGroup):
    waiting_title          = State()
    waiting_schedule_type  = State()
    waiting_schedule_value = State()   # weekly/monthly → callback; once → text
    waiting_time           = State()   # preset → callback; custom → text
    waiting_target         = State()
    waiting_confirmation   = State()


class ReminderNavCallback(CallbackData, prefix="rem_nav"):
    action: str  # cancel | back | save


class ReminderScheduleCallback(CallbackData, prefix="rem_sch"):
    type: str  # daily | weekly | monthly | once


class ReminderValueCallback(CallbackData, prefix="rem_val"):
    value: str  # weekday "0"–"6" or day "1"–"28"


class ReminderTimeCallback(CallbackData, prefix="rem_time"):
    time: str  # "08:00" … "22:00" | "custom"


class ReminderTargetCallback(CallbackData, prefix="rem_tgt"):
    target: str   # private | group
    chat_id: int = 0
