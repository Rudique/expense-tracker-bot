from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.fsm.category import CatNavCallback


def _btn(text: str, action: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=CatNavCallback(action=action).pack())


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("❌ Cancel", "cancel")]])


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("💾 Save", "save")],
        [_btn("← Back", "back")],
        [_btn("❌ Cancel", "cancel")],
    ])
