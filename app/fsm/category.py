from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class AddCategory(StatesGroup):
    waiting_input        = State()
    waiting_confirmation = State()


class CatNavCallback(CallbackData, prefix="cat_nav"):
    action: str  # cancel | back | save
