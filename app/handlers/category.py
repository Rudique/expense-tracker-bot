import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = structlog.get_logger()

from app.fsm.category import AddCategory, CatNavCallback
from app.keyboards.category import cancel_kb, confirm_kb
from app.services.category_service import CategoryService
from app.services.message_service import delete_message, edit_message
from app.texts.category import (
    cancelled_text,
    confirm_text,
    input_invalid,
    input_prompt,
    success_text,
)

router = Router()


@router.message(Command("add_category"))
async def cmd_add_category(message: Message, state: FSMContext) -> None:
    await state.set_state(AddCategory.waiting_input)
    sent = await message.answer(input_prompt(), reply_markup=cancel_kb())
    await state.update_data(prompt_msg_id=sent.message_id)


@router.message(AddCategory.waiting_input)
async def process_input(message: Message, state: FSMContext) -> None:
    await delete_message(message)
    data = await state.get_data()

    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await edit_message(message, data["prompt_msg_id"], input_invalid(), cancel_kb())
        return

    emoji, name = parts
    await state.update_data(emoji=emoji, name=name)
    await state.set_state(AddCategory.waiting_confirmation)

    text = confirm_text(emoji, name)
    if not await edit_message(message, data["prompt_msg_id"], text, confirm_kb()):
        sent = await message.answer(text, reply_markup=confirm_kb())
        await state.update_data(prompt_msg_id=sent.message_id)


@router.callback_query(CatNavCallback.filter())
async def on_nav(
    callback: CallbackQuery,
    callback_data: CatNavCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    action = callback_data.action

    if action == "cancel":
        await state.clear()
        await callback.message.edit_text(cancelled_text())

    elif action == "back":
        await state.set_state(AddCategory.waiting_input)
        await callback.message.edit_text(input_prompt(), reply_markup=cancel_kb())

    elif action == "save":
        data = await state.get_data()
        async with session_factory() as session:
            category = await CategoryService.create(
                session=session, emoji=data["emoji"], name=data["name"]
            )
        logger.info("category_created", category_id=category.id, emoji=data["emoji"], name=data["name"])
        await state.clear()
        await callback.message.edit_text(success_text(category.emoji, category.name))


@router.message(Command("categories"))
async def cmd_categories(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        categories = await CategoryService.get_all(session=session)

    if not categories:
        await message.answer("📭 No categories yet.\n\nAdd one with /add_category")
        return

    lines = "\n".join(f"{c.emoji} {c.name}" for c in categories)
    await message.answer(f"📋 <b>Your categories</b>\n\n{lines}")
