from decimal import Decimal, InvalidOperation
from typing import Optional

from aiogram import F, Router
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

router = Router()


class AddTransaction(StatesGroup):
    waiting_amount = State()
    waiting_category = State()
    waiting_comment = State()


class CategoryCallback(CallbackData, prefix="txn_cat"):
    id: int
    emoji: str
    name: str


class NavCallback(CallbackData, prefix="txn_nav"):
    action: str  # cancel | back | skip


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


# ── Step 1: amount ─────────────────────────────────────────────────────────────

@router.message(Command("add_transaction"))
async def cmd_add_transaction(message: Message, state: FSMContext) -> None:
    await state.set_state(AddTransaction.waiting_amount)
    is_shared = message.chat.type != ChatType.PRIVATE
    sent = await message.answer(
        "💰 <b>How much did you spend?</b>\n\nEnter the amount:",
        reply_markup=_cancel_kb(),
    )
    await state.update_data(prompt_msg_id=sent.message_id, is_shared=is_shared)


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
        await message.answer(
            "⚠️ Please enter a valid positive number.\n\nExample: <b>1500</b> or <b>9.99</b>",
            reply_markup=_cancel_kb(),
        )
        return

    async with session_factory() as session:
        categories = await CategoryService.get_all(session=session)

    if not categories:
        await state.clear()
        await message.answer("📭 You have no categories yet.\n\nAdd one first with /add_category")
        return

    data = await state.get_data()
    await state.update_data(amount=str(amount))
    await state.set_state(AddTransaction.waiting_category)
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["prompt_msg_id"],
        text="📂 <b>Select a category:</b>",
        reply_markup=_category_kb(categories),
    )


# ── Step 2: category ───────────────────────────────────────────────────────────

@router.callback_query(CategoryCallback.filter(), AddTransaction.waiting_category)
async def process_category(
    callback: CallbackQuery,
    callback_data: CategoryCallback,
    state: FSMContext,
) -> None:
    await state.update_data(
        category_id=callback_data.id,
        category_label=f"{callback_data.emoji} {callback_data.name}",
    )
    await state.set_state(AddTransaction.waiting_comment)
    await callback.message.edit_text(
        f"📂 Category: <b>{callback_data.emoji} {callback_data.name}</b>\n\n"
        "💬 <b>Add a comment:</b>",
        reply_markup=_comment_kb(),
    )
    await callback.answer()


# ── Step 3: comment ────────────────────────────────────────────────────────────

@router.message(AddTransaction.waiting_comment)
async def process_comment(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    data = await state.get_data()
    transaction = await _save(session_factory, data, comment=message.text.strip())
    await state.clear()
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["prompt_msg_id"],
        text=_success_text(transaction, data["category_label"]),
    )


# ── Navigation ─────────────────────────────────────────────────────────────────

@router.callback_query(NavCallback.filter(F.action == "cancel"))
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if await state.get_state() is None:
        await callback.answer("This action is no longer available.")
        return
    await state.clear()
    await callback.message.edit_text("❌ <b>Transaction cancelled.</b>")
    await callback.answer()


@router.callback_query(NavCallback.filter(F.action == "back"), AddTransaction.waiting_category)
async def on_back_to_amount(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddTransaction.waiting_amount)
    await callback.message.edit_text(
        "💰 <b>How much did you spend?</b>\n\nEnter the amount:",
        reply_markup=_cancel_kb(),
    )
    await callback.answer()


@router.callback_query(NavCallback.filter(F.action == "back"), AddTransaction.waiting_comment)
async def on_back_to_category(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        categories = await CategoryService.get_all(session=session)
    await state.set_state(AddTransaction.waiting_category)
    await callback.message.edit_text(
        "📂 <b>Select a category:</b>",
        reply_markup=_category_kb(categories),
    )
    await callback.answer()


@router.callback_query(NavCallback.filter(F.action == "skip"), AddTransaction.waiting_comment)
async def on_skip_comment(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    data = await state.get_data()
    transaction = await _save(session_factory, data, comment=None)
    await state.clear()
    await callback.message.edit_text(_success_text(transaction, data["category_label"]))
    await callback.answer()


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _save(
    session_factory: async_sessionmaker[AsyncSession],
    data: dict,
    comment: Optional[str],
) -> Transaction:
    async with session_factory() as session:
        transaction = await TransactionService.create(
            session=session,
            amount=Decimal(data["amount"]),
            category_id=data["category_id"],
            comment=comment,
            is_shared=data["is_shared"],
        )
    return transaction


def _success_text(transaction, category_label: str) -> str:
    comment_line = f"\n💬 {transaction.comment}" if transaction.comment else ""
    return (
        f"✅ <b>Transaction saved!</b>\n\n"
        f"💰 Amount: <b>{transaction.amount}</b>\n"
        f"📂 Category: <b>{category_label}</b>"
        f"{comment_line}"
    )
