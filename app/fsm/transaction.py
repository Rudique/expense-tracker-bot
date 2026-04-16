from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class AddTransaction(StatesGroup):
    waiting_amount = State()
    waiting_category = State()
    waiting_comment = State()
    waiting_confirmation = State()


class CategoryCallback(CallbackData, prefix="txn_cat"):
    id: int
    emoji: str
    name: str


class NavCallback(CallbackData, prefix="txn_nav"):
    action: str  # cancel | back | skip | save
