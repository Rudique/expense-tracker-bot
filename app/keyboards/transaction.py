from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.fsm.transaction import CategoryCallback, NavCallback


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❌ Cancel", callback_data=NavCallback(action="cancel").pack()),
    ]])


def category_kb(categories: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"{c.emoji} {c.name}",
            callback_data=CategoryCallback(id=c.id, emoji=c.emoji, name=c.name).pack(),
        )]
        for c in categories
    ]
    rows.append([
        InlineKeyboardButton(text="← Back", callback_data=NavCallback(action="back").pack()),
        InlineKeyboardButton(text="❌ Cancel", callback_data=NavCallback(action="cancel").pack()),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def comment_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Skip", callback_data=NavCallback(action="skip").pack())],
        [
            InlineKeyboardButton(text="← Back", callback_data=NavCallback(action="back").pack()),
            InlineKeyboardButton(text="❌ Cancel", callback_data=NavCallback(action="cancel").pack()),
        ],
    ])


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💾 Save", callback_data=NavCallback(action="save").pack())],
        [InlineKeyboardButton(text="← Back", callback_data=NavCallback(action="back").pack())],
        [InlineKeyboardButton(text="❌ Cancel", callback_data=NavCallback(action="cancel").pack())],
    ])
