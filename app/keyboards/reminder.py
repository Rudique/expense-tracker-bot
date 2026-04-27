from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.fsm.reminder import (
    ReminderNavCallback,
    ReminderScheduleCallback,
    ReminderTargetCallback,
    ReminderTimeCallback,
    ReminderValueCallback,
)


def _nav(text: str, action: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=ReminderNavCallback(action=action).pack())


def _back() -> list[InlineKeyboardButton]:
    return [_nav("← Back", "back")]


def _cancel() -> list[InlineKeyboardButton]:
    return [_nav("❌ Cancel", "cancel")]


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[_cancel()])


def back_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[_back(), _cancel()])


def schedule_type_kb() -> InlineKeyboardMarkup:
    def s(text: str, t: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=ReminderScheduleCallback(type=t).pack())

    return InlineKeyboardMarkup(inline_keyboard=[
        [s("📅 Daily", "daily"),     s("📆 Weekly", "weekly")],
        [s("🗓 Monthly", "monthly"),  s("📌 One-time", "once")],
        _back(),
        _cancel(),
    ])


_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def weekly_day_kb() -> InlineKeyboardMarkup:
    def d(label: str, idx: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=label, callback_data=ReminderValueCallback(value=str(idx)).pack())

    return InlineKeyboardMarkup(inline_keyboard=[
        [d(day, i) for i, day in enumerate(_DAYS[:4])],
        [d(day, i + 4) for i, day in enumerate(_DAYS[4:])],
        _back(),
        _cancel(),
    ])


def monthly_day_kb() -> InlineKeyboardMarkup:
    def d(n: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=str(n), callback_data=ReminderValueCallback(value=str(n)).pack())

    rows = [[d(n) for n in range(start, min(start + 7, 29))] for start in range(1, 29, 7)]
    rows += [_back(), _cancel()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Stored without colon in callback data (aiogram uses ':' as separator)
_PRESET_TIMES = ["0800", "1200", "1800", "2000", "2200"]


def _fmt(t: str) -> str:
    return f"{t[:2]}:{t[2:]}"


def time_kb() -> InlineKeyboardMarkup:
    def t(value: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=_fmt(value), callback_data=ReminderTimeCallback(time=value).pack())

    def custom() -> InlineKeyboardButton:
        return InlineKeyboardButton(text="⌨️ Other", callback_data=ReminderTimeCallback(time="custom").pack())

    rows = [[t(_PRESET_TIMES[i]), t(_PRESET_TIMES[i + 1])] for i in range(0, 4, 2)]
    rows.append([t(_PRESET_TIMES[4]), custom()])
    rows += [_back(), _cancel()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def target_kb(groups: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text="💬 Private chat",
        callback_data=ReminderTargetCallback(target="private").pack(),
    )]]
    for g in groups:
        rows.append([InlineKeyboardButton(
            text=f"📣 {g.title}/Reminders",
            callback_data=ReminderTargetCallback(target="group", chat_id=g.chat_id).pack(),
        )])
    rows += [_back(), _cancel()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_nav("💾 Save", "save")],
        _back(),
        _cancel(),
    ])
