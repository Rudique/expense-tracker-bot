from decimal import Decimal, InvalidOperation

import structlog
from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = structlog.get_logger()

from app.fsm.transaction import AddTransaction, CategoryCallback, NavCallback
from app.keyboards.transaction import cancel_kb, category_kb, comment_kb, confirm_kb
from app.services.category_service import CategoryService
from app.services.message_service import delete_message, edit_message
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService
from app.texts.transaction import (
    amount_invalid,
    amount_prompt,
    cancelled_text,
    category_prompt,
    comment_prompt,
    confirm_text,
    no_categories_text,
    success_text,
)

router = Router()


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
    sent = await message.answer(amount_prompt(), reply_markup=cancel_kb())
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
        await delete_message(message)
        data = await state.get_data()
        await edit_message(message, data["prompt_msg_id"], amount_invalid(), cancel_kb())
        return

    async with session_factory() as session:
        categories = await CategoryService.get_all(session=session)

    if not categories:
        await state.clear()
        await message.answer(no_categories_text())
        return

    await delete_message(message)
    data = await state.get_data()
    await state.update_data(amount=str(amount))
    await state.set_state(AddTransaction.waiting_category)

    text = category_prompt(str(amount))
    kb = category_kb(categories)
    if not await edit_message(message, data["prompt_msg_id"], text, kb):
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
    label = f"{callback_data.emoji} {callback_data.name}"
    await state.update_data(category_id=callback_data.id, category_label=label)
    await state.set_state(AddTransaction.waiting_comment)
    await callback.message.edit_text(comment_prompt(data["amount"], label), reply_markup=comment_kb())
    await callback.answer()


# ── Step 3: comment ────────────────────────────────────────────────────────────

@router.message(AddTransaction.waiting_comment)
async def process_comment(
    message: Message,
    state: FSMContext,
) -> None:
    await delete_message(message)
    data = await state.get_data()
    comment = message.text.strip()
    await state.update_data(comment=comment)
    await state.set_state(AddTransaction.waiting_confirmation)

    text = confirm_text(data["amount"], data["category_label"], comment)
    if not await edit_message(message, data["prompt_msg_id"], text, confirm_kb()):
        sent = await message.answer(text, reply_markup=confirm_kb())
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
        await callback.message.edit_text(cancelled_text())

    elif action == "back":
        data = await state.get_data()

        if current_state == AddTransaction.waiting_category:
            await state.set_state(AddTransaction.waiting_amount)
            await callback.message.edit_text(amount_prompt(), reply_markup=cancel_kb())

        elif current_state == AddTransaction.waiting_comment:
            async with session_factory() as session:
                categories = await CategoryService.get_all(session=session)
            await state.set_state(AddTransaction.waiting_category)
            await callback.message.edit_text(
                category_prompt(data["amount"]), reply_markup=category_kb(categories)
            )

        elif current_state == AddTransaction.waiting_confirmation:
            await state.set_state(AddTransaction.waiting_comment)
            await callback.message.edit_text(
                comment_prompt(data["amount"], data["category_label"]), reply_markup=comment_kb()
            )

    elif action == "skip":
        if current_state == AddTransaction.waiting_comment:
            data = await state.get_data()
            await state.update_data(comment=None)
            await state.set_state(AddTransaction.waiting_confirmation)
            await callback.message.edit_text(
                confirm_text(data["amount"], data["category_label"], None), reply_markup=confirm_kb()
            )

    elif action == "save":
        if current_state == AddTransaction.waiting_confirmation:
            data = await state.get_data()
            async with session_factory() as session:
                transaction = await TransactionService.create(
                    session=session,
                    user_id=data["user_id"],
                    amount=Decimal(data["amount"]),
                    category_id=data["category_id"],
                    comment=data.get("comment"),
                    is_shared=data["is_shared"],
                )
            logger.info(
                "transaction_created",
                transaction_id=transaction.id,
                amount=str(data["amount"]),
                category=data["category_label"],
                is_shared=data["is_shared"],
            )
            await state.clear()
            await callback.message.edit_text(success_text(transaction, data["category_label"]))

