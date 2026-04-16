from decimal import Decimal, InvalidOperation
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatType
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.transaction import Transaction
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService

router = Router()


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


# ── Keyboards ──────────────────────────────────────────────────────────────────

def _cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❌ Cancel", callback_data=NavCallback(action="cancel").pack()),
    ]])


def _category_kb(categories: list) -> InlineKeyboardMarkup:
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


def _comment_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Skip", callback_data=NavCallback(action="skip").pack())],
        [
            InlineKeyboardButton(text="← Back", callback_data=NavCallback(action="back").pack()),
            InlineKeyboardButton(text="❌ Cancel", callback_data=NavCallback(action="cancel").pack()),
        ],
    ])


def _confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💾 Save", callback_data=NavCallback(action="save").pack())],
        [InlineKeyboardButton(text="← Back", callback_data=NavCallback(action="back").pack())],
        [InlineKeyboardButton(text="❌ Cancel", callback_data=NavCallback(action="cancel").pack())],
    ])


# ── Text builders ──────────────────────────────────────────────────────────────

def _category_prompt(amount: str) -> str:
    return f"💰 Amount: <b>{amount}</b>\n\n📂 <b>Select a category:</b>"


def _comment_prompt(amount: str, category_label: str) -> str:
    return (
        f"💰 Amount: <b>{amount}</b>\n"
        f"📂 Category: <b>{category_label}</b>\n\n"
        "💬 <b>Add a comment:</b>"
    )


def _confirm_text(amount: str, category_label: str, comment: Optional[str]) -> str:
    lines = [
        f"💰 Amount: <b>{amount}</b>",
        f"📂 Category: <b>{category_label}</b>",
    ]
    if comment:
        lines.append(f"💬 Comment: <b>{comment}</b>")
    lines.append("\nReady to save?")
    return "\n".join(lines)


def _success_text(transaction: Transaction, category_label: str) -> str:
    comment_line = f"\n💬 {transaction.comment}" if transaction.comment else ""
    return (
        f"✅ <b>Transaction saved!</b>\n\n"
        f"💰 Amount: <b>{transaction.amount}</b>\n"
        f"📂 Category: <b>{category_label}</b>"
        f"{comment_line}"
    )


# ── Step 1: amount ─────────────────────────────────────────────────────────────

@router.message(Command("add_transaction"))
async def cmd_add_transaction(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tg_user = message.from_user
    async with session_factory() as session:
        user, _ = await UserService.create_or_update_from_telegram(
            session=session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )

    await state.set_state(AddTransaction.waiting_amount)
    is_shared = message.chat.type != ChatType.PRIVATE
    sent = await message.answer(
        "💰 <b>How much did you spend?</b>\n\nEnter the amount:",
        reply_markup=_cancel_kb(),
    )
    await state.update_data(prompt_msg_id=sent.message_id, is_shared=is_shared, user_id=user.id)


@router.message(AddTransaction.waiting_amount)
async def process_amount(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    try:
        amount = Decimal(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        try:
            await message.delete()
        except Exception:
            pass
        data = await state.get_data()
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["prompt_msg_id"],
                text="⚠️ Please enter a valid positive number.\n\nExample: <b>1500</b> or <b>9.99</b>",
                reply_markup=_cancel_kb(),
            )
        except Exception:
            pass
        return

    async with session_factory() as session:
        categories = await CategoryService.get_all(session=session)

    if not categories:
        await state.clear()
        await message.answer("📭 You have no categories yet.\n\nAdd one first with /add_category")
        return

    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    await state.update_data(amount=str(amount))
    await state.set_state(AddTransaction.waiting_category)

    text = _category_prompt(str(amount))
    kb = _category_kb(categories)
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data["prompt_msg_id"],
            text=text,
            reply_markup=kb,
        )
    except Exception:
        sent = await message.answer(text, reply_markup=kb)
        await state.update_data(prompt_msg_id=sent.message_id)


# ── Step 2: category ───────────────────────────────────────────────────────────

@router.callback_query(CategoryCallback.filter(), AddTransaction.waiting_category)
async def process_category(
    callback: CallbackQuery,
    callback_data: CategoryCallback,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    category_label = f"{callback_data.emoji} {callback_data.name}"
    await state.update_data(category_id=callback_data.id, category_label=category_label)
    await state.set_state(AddTransaction.waiting_comment)
    await callback.message.edit_text(
        _comment_prompt(data["amount"], category_label),
        reply_markup=_comment_kb(),
    )
    await callback.answer()


# ── Step 3: comment ────────────────────────────────────────────────────────────

@router.message(AddTransaction.waiting_comment)
async def process_comment(
    message: Message,
    state: FSMContext,
) -> None:
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    comment = message.text.strip()
    await state.update_data(comment=comment)
    await state.set_state(AddTransaction.waiting_confirmation)

    text = _confirm_text(data["amount"], data["category_label"], comment)
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data["prompt_msg_id"],
            text=text,
            reply_markup=_confirm_kb(),
        )
    except Exception:
        sent = await message.answer(text, reply_markup=_confirm_kb())
        await state.update_data(prompt_msg_id=sent.message_id)


# ── Navigation ─────────────────────────────────────────────────────────────────

@router.callback_query(NavCallback.filter())
async def on_nav(
    callback: CallbackQuery,
    callback_data: NavCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()

    action = callback_data.action
    current_state = await state.get_state()

    if action == "cancel":
        if current_state is None:
            return
        await state.clear()
        await callback.message.edit_text("❌ <b>Transaction cancelled.</b>")

    elif action == "back":
        data = await state.get_data()

        if current_state == AddTransaction.waiting_category:
            await state.set_state(AddTransaction.waiting_amount)
            await callback.message.edit_text(
                "💰 <b>How much did you spend?</b>\n\nEnter the amount:",
                reply_markup=_cancel_kb(),
            )

        elif current_state == AddTransaction.waiting_comment:
            async with session_factory() as session:
                categories = await CategoryService.get_all(session=session)
            await state.set_state(AddTransaction.waiting_category)
            await callback.message.edit_text(
                _category_prompt(data["amount"]),
                reply_markup=_category_kb(categories),
            )

        elif current_state == AddTransaction.waiting_confirmation:
            await state.set_state(AddTransaction.waiting_comment)
            await callback.message.edit_text(
                _comment_prompt(data["amount"], data["category_label"]),
                reply_markup=_comment_kb(),
            )

    elif action == "skip":
        if current_state == AddTransaction.waiting_comment:
            data = await state.get_data()
            await state.update_data(comment=None)
            await state.set_state(AddTransaction.waiting_confirmation)
            await callback.message.edit_text(
                _confirm_text(data["amount"], data["category_label"], None),
                reply_markup=_confirm_kb(),
            )

    elif action == "save":
        if current_state == AddTransaction.waiting_confirmation:
            data = await state.get_data()
            transaction = await _save(session_factory, data, comment=data.get("comment"))
            await state.clear()
            await callback.message.edit_text(
                _success_text(transaction, data["category_label"])
            )


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _save(
    session_factory: async_sessionmaker[AsyncSession],
    data: dict,
    comment: Optional[str],
) -> Transaction:
    async with session_factory() as session:
        transaction = await TransactionService.create(
            session=session,
            user_id=data["user_id"],
            amount=Decimal(data["amount"]),
            category_id=data["category_id"],
            comment=comment,
            is_shared=data["is_shared"],
        )
    return transaction
