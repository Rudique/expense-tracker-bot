import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = structlog.get_logger()

from app.fsm.reminder import (
    AddReminder,
    ReminderActionCallback,
    ReminderListCallback,
    ReminderNavCallback,
    ReminderScheduleCallback,
    ReminderTargetCallback,
    ReminderTimeCallback,
    ReminderValueCallback,
)
from app.keyboards.reminder import (
    back_cancel_kb,
    cancel_kb,
    confirm_delete_kb,
    confirm_kb,
    monthly_day_kb,
    reminder_detail_kb,
    reminder_list_kb,
    schedule_type_kb,
    target_kb,
    time_kb,
    weekly_day_kb,
)
from app.scheduler import register_reminder, unregister_reminder
from app.services.group_service import GroupService
from app.services.message_service import delete_message, edit_message
from app.services.reminder_service import ReminderService
from app.services.user_service import UserService
from app.texts.reminder import (
    cancelled_text,
    confirm_text,
    monthly_day_prompt,
    my_reminders_text,
    once_date_invalid,
    once_date_prompt,
    reminder_deleted_text,
    reminder_detail_text,
    schedule_label,
    schedule_type_prompt,
    success_text,
    target_prompt,
    time_custom_prompt,
    time_invalid,
    time_prompt,
    title_prompt,
    updated_text,
    weekly_day_prompt,
)

router = Router()


async def _show_target_step(
    message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    data = await state.get_data()
    sched = schedule_label(data["schedule_type"], data.get("schedule_value"))
    async with session_factory() as session:
        groups = await GroupService.get_all(session)
    await state.set_state(AddReminder.waiting_target)
    await message.edit_text(
        target_prompt(data["title"], sched, data["send_time"]),
        reply_markup=target_kb(groups),
    )


# ── /add_reminder ──────────────────────────────────────────────────────────────

@router.message(Command("add_reminder"))
async def cmd_add_reminder(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        user = await UserService.get_or_create(session, message.from_user)
        await GroupService.register_from_message(session, message)

    await state.set_state(AddReminder.waiting_title)
    sent = await message.answer(title_prompt(), reply_markup=cancel_kb())
    await state.update_data(
        prompt_msg_id=sent.message_id,
        user_id=user.id,
        telegram_user_id=message.from_user.id,
    )


# ── Step 1: title ──────────────────────────────────────────────────────────────

@router.message(AddReminder.waiting_title)
async def process_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    await delete_message(message)
    data = await state.get_data()
    await state.update_data(title=title)
    await state.set_state(AddReminder.waiting_schedule_type)

    text = schedule_type_prompt(title)
    if not await edit_message(message, data["prompt_msg_id"], text, schedule_type_kb()):
        sent = await message.answer(text, reply_markup=schedule_type_kb())
        await state.update_data(prompt_msg_id=sent.message_id)


# ── Step 2: schedule type ──────────────────────────────────────────────────────

@router.callback_query(ReminderScheduleCallback.filter(), AddReminder.waiting_schedule_type)
async def process_schedule_type(
    callback: CallbackQuery,
    callback_data: ReminderScheduleCallback,
    state: FSMContext,
) -> None:
    await callback.answer()
    stype = callback_data.type
    data = await state.get_data()
    await state.update_data(schedule_type=stype, schedule_value=None)

    if stype == "daily":
        await state.set_state(AddReminder.waiting_time)
        await callback.message.edit_text(
            time_prompt(data["title"], schedule_label(stype, None)), reply_markup=time_kb()
        )
    elif stype == "weekly":
        await state.set_state(AddReminder.waiting_schedule_value)
        await callback.message.edit_text(weekly_day_prompt(data["title"]), reply_markup=weekly_day_kb())
    elif stype == "monthly":
        await state.set_state(AddReminder.waiting_schedule_value)
        await callback.message.edit_text(monthly_day_prompt(data["title"]), reply_markup=monthly_day_kb())
    elif stype == "once":
        await state.set_state(AddReminder.waiting_schedule_value)
        await callback.message.edit_text(once_date_prompt(data["title"]), reply_markup=back_cancel_kb())


# ── Step 3: schedule value ─────────────────────────────────────────────────────

@router.callback_query(ReminderValueCallback.filter(), AddReminder.waiting_schedule_value)
async def process_schedule_value(
    callback: CallbackQuery,
    callback_data: ReminderValueCallback,
    state: FSMContext,
) -> None:
    await callback.answer()
    data = await state.get_data()
    await state.update_data(schedule_value=callback_data.value)
    await state.set_state(AddReminder.waiting_time)
    sched = schedule_label(data["schedule_type"], callback_data.value)
    await callback.message.edit_text(time_prompt(data["title"], sched), reply_markup=time_kb())


@router.message(AddReminder.waiting_schedule_value)  # "once" date text input
async def process_once_date(message: Message, state: FSMContext) -> None:
    await delete_message(message)
    data = await state.get_data()
    date_str = ReminderService.parse_date(message.text)

    if not date_str:
        await edit_message(message, data["prompt_msg_id"], once_date_invalid(data["title"]), back_cancel_kb())
        return

    await state.update_data(schedule_value=date_str)
    await state.set_state(AddReminder.waiting_time)
    text = time_prompt(data["title"], schedule_label("once", date_str))
    if not await edit_message(message, data["prompt_msg_id"], text, time_kb()):
        sent = await message.answer(text, reply_markup=time_kb())
        await state.update_data(prompt_msg_id=sent.message_id)


# ── Step 4: time ───────────────────────────────────────────────────────────────

@router.callback_query(ReminderTimeCallback.filter(), AddReminder.waiting_time)
async def process_time_cb(
    callback: CallbackQuery,
    callback_data: ReminderTimeCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    data = await state.get_data()

    if callback_data.time == "custom":
        await state.update_data(time_awaiting_custom=True)
        sched = schedule_label(data["schedule_type"], data.get("schedule_value"))
        await callback.message.edit_text(
            time_custom_prompt(data["title"], sched), reply_markup=back_cancel_kb()
        )
        return

    send_time = f"{callback_data.time[:2]}:{callback_data.time[2:]}"
    await state.update_data(send_time=send_time, time_awaiting_custom=False)
    await _show_target_step(callback.message, state, session_factory)


@router.message(AddReminder.waiting_time)
async def process_time_text(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await delete_message(message)
    data = await state.get_data()
    parsed = ReminderService.parse_time(message.text)

    if not parsed:
        sched = schedule_label(data["schedule_type"], data.get("schedule_value"))
        await edit_message(message, data["prompt_msg_id"], time_invalid(data["title"], sched), back_cancel_kb())
        return

    await state.update_data(send_time=parsed, time_awaiting_custom=False)
    async with session_factory() as session:
        groups = await GroupService.get_all(session)
    await state.set_state(AddReminder.waiting_target)
    sched = schedule_label(data["schedule_type"], data.get("schedule_value"))
    text = target_prompt(data["title"], sched, parsed)
    if not await edit_message(message, data["prompt_msg_id"], text, target_kb(groups)):
        sent = await message.answer(text, reply_markup=target_kb(groups))
        await state.update_data(prompt_msg_id=sent.message_id)


# ── Step 5: target ─────────────────────────────────────────────────────────────

@router.callback_query(ReminderTargetCallback.filter(), AddReminder.waiting_target)
async def process_target(
    callback: CallbackQuery,
    callback_data: ReminderTargetCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    data = await state.get_data()

    if callback_data.target == "group":
        async with session_factory() as session:
            thread_id, target_label = await GroupService.resolve_group_target(
                session, callback_data.chat_id
            )
        if thread_id is None:
            await callback.answer(
                "⚠️ Reminders topic not set.\nRun /set_reminders_topic inside the topic first.",
                show_alert=True,
            )
            return
        await state.update_data(
            target="group_topic",
            target_chat_id=callback_data.chat_id,
            target_thread_id=thread_id,
            target_label=target_label,
        )
    else:
        await state.update_data(
            target="private",
            target_chat_id=None,
            target_thread_id=None,
            target_label="💬 Private chat",
        )

    data = await state.get_data()
    sched = schedule_label(data["schedule_type"], data.get("schedule_value"))
    await state.set_state(AddReminder.waiting_confirmation)
    await callback.message.edit_text(
        confirm_text(data["title"], sched, data["send_time"], data["target_label"]),
        reply_markup=confirm_kb(),
    )


# ── Navigation ─────────────────────────────────────────────────────────────────

@router.callback_query(ReminderNavCallback.filter())
async def on_nav(
    callback: CallbackQuery,
    callback_data: ReminderNavCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    action = callback_data.action
    current = await state.get_state()
    data = await state.get_data()

    if action == "cancel":
        await state.clear()
        await callback.message.edit_text(cancelled_text())
        return

    if action == "back":
        if current == AddReminder.waiting_schedule_type:
            await state.set_state(AddReminder.waiting_title)
            await callback.message.edit_text(title_prompt(), reply_markup=cancel_kb())

        elif current == AddReminder.waiting_schedule_value:
            await state.set_state(AddReminder.waiting_schedule_type)
            await callback.message.edit_text(schedule_type_prompt(data["title"]), reply_markup=schedule_type_kb())

        elif current == AddReminder.waiting_time:
            stype = data["schedule_type"]
            if data.get("time_awaiting_custom"):
                await state.update_data(time_awaiting_custom=False)
                sched = schedule_label(stype, data.get("schedule_value"))
                await callback.message.edit_text(time_prompt(data["title"], sched), reply_markup=time_kb())
            elif stype == "daily":
                await state.set_state(AddReminder.waiting_schedule_type)
                await callback.message.edit_text(schedule_type_prompt(data["title"]), reply_markup=schedule_type_kb())
            else:
                await state.set_state(AddReminder.waiting_schedule_value)
                if stype == "weekly":
                    await callback.message.edit_text(weekly_day_prompt(data["title"]), reply_markup=weekly_day_kb())
                elif stype == "monthly":
                    await callback.message.edit_text(monthly_day_prompt(data["title"]), reply_markup=monthly_day_kb())
                else:
                    await callback.message.edit_text(once_date_prompt(data["title"]), reply_markup=back_cancel_kb())

        elif current == AddReminder.waiting_target:
            sched = schedule_label(data["schedule_type"], data.get("schedule_value"))
            await state.set_state(AddReminder.waiting_time)
            await callback.message.edit_text(time_prompt(data["title"], sched), reply_markup=time_kb())

        elif current == AddReminder.waiting_confirmation:
            await _show_target_step(callback.message, state, session_factory)

    elif action == "save" and current == AddReminder.waiting_confirmation:
        editing_id = data.get("editing_reminder_id")
        sched = schedule_label(data["schedule_type"], data.get("schedule_value"))
        async with session_factory() as session:
            if editing_id:
                unregister_reminder(editing_id)
                reminder = await ReminderService.update(
                    session=session,
                    reminder_id=editing_id,
                    title=data["title"],
                    schedule_type=data["schedule_type"],
                    schedule_value=data.get("schedule_value"),
                    send_time=data["send_time"],
                    target=data["target"],
                    chat_id=data.get("target_chat_id"),
                    thread_id=data.get("target_thread_id"),
                )
                register_reminder(callback.bot, session_factory, reminder)
                logger.info(
                    "reminder_updated",
                    reminder_id=editing_id,
                    title=data["title"],
                    schedule=sched,
                    send_time=data["send_time"],
                    target=data["target"],
                )
                await state.clear()
                await callback.message.edit_text(
                    updated_text(data["title"], sched, data["send_time"], data["target_label"])
                )
            else:
                reminder = await ReminderService.create(
                    session=session,
                    user_id=data["user_id"],
                    telegram_user_id=data["telegram_user_id"],
                    title=data["title"],
                    schedule_type=data["schedule_type"],
                    schedule_value=data.get("schedule_value"),
                    send_time=data["send_time"],
                    target=data["target"],
                    chat_id=data.get("target_chat_id"),
                    thread_id=data.get("target_thread_id"),
                )
                register_reminder(callback.bot, session_factory, reminder)
                logger.info(
                    "reminder_created",
                    reminder_id=reminder.id,
                    title=data["title"],
                    schedule=sched,
                    send_time=data["send_time"],
                    target=data["target"],
                )
                await state.clear()
                await callback.message.edit_text(
                    success_text(data["title"], sched, data["send_time"], data["target_label"])
                )


# ── /my_reminders ──────────────────────────────────────────────────────────────

@router.message(Command("my_reminders"))
async def cmd_my_reminders(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await state.clear()
    async with session_factory() as session:
        user = await UserService.get_or_create(session, message.from_user)
        reminders = await ReminderService.get_by_user(session, user.id)
    await message.answer(
        my_reminders_text(len(reminders)),
        reply_markup=reminder_list_kb(reminders) if reminders else None,
    )


@router.callback_query(ReminderListCallback.filter())
async def on_reminder_select(
    callback: CallbackQuery,
    callback_data: ReminderListCallback,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    async with session_factory() as session:
        reminder = await ReminderService.get_by_id(session, callback_data.reminder_id)
    if not reminder:
        await callback.message.edit_text("⚠️ Reminder not found.")
        return
    sched = schedule_label(reminder.schedule_type, reminder.schedule_value)
    target_label = "💬 Private chat" if reminder.target == "private" else "📣 Group/Reminders"
    await callback.message.edit_text(
        reminder_detail_text(reminder.title, sched, reminder.send_time, target_label),
        reply_markup=reminder_detail_kb(reminder.id),
    )


@router.callback_query(ReminderActionCallback.filter())
async def on_reminder_action(
    callback: CallbackQuery,
    callback_data: ReminderActionCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await callback.answer()
    action = callback_data.action
    reminder_id = callback_data.reminder_id

    if action == "back_to_list":
        async with session_factory() as session:
            user = await UserService.get_or_create(session, callback.from_user)
            reminders = await ReminderService.get_by_user(session, user.id)
        await callback.message.edit_text(
            my_reminders_text(len(reminders)),
            reply_markup=reminder_list_kb(reminders) if reminders else None,
        )

    elif action == "detail":
        async with session_factory() as session:
            reminder = await ReminderService.get_by_id(session, reminder_id)
        if not reminder:
            await callback.message.edit_text("⚠️ Reminder not found.")
            return
        sched = schedule_label(reminder.schedule_type, reminder.schedule_value)
        target_label = "💬 Private chat" if reminder.target == "private" else "📣 Group/Reminders"
        await callback.message.edit_text(
            reminder_detail_text(reminder.title, sched, reminder.send_time, target_label),
            reply_markup=reminder_detail_kb(reminder.id),
        )

    elif action == "delete":
        async with session_factory() as session:
            reminder = await ReminderService.get_by_id(session, reminder_id)
        if not reminder:
            await callback.message.edit_text("⚠️ Reminder not found.")
            return
        await callback.message.edit_text(
            f"🗑 Delete <b>{reminder.title}</b>?\n\nThis cannot be undone.",
            reply_markup=confirm_delete_kb(reminder_id),
        )

    elif action == "confirm_delete":
        async with session_factory() as session:
            reminder = await ReminderService.get_by_id(session, reminder_id)
            title = reminder.title if reminder else "Reminder"
            await ReminderService.delete(session, reminder_id)
        unregister_reminder(reminder_id)
        logger.info("reminder_deleted", reminder_id=reminder_id, title=title)
        await callback.message.edit_text(reminder_deleted_text(title))

    elif action == "edit":
        async with session_factory() as session:
            reminder = await ReminderService.get_by_id(session, reminder_id)
            user = await UserService.get_or_create(session, callback.from_user)
        if not reminder:
            await callback.message.edit_text("⚠️ Reminder not found.")
            return
        target_label = "💬 Private chat" if reminder.target == "private" else "📣 Group/Reminders"
        sched = schedule_label(reminder.schedule_type, reminder.schedule_value)
        await state.update_data(
            editing_reminder_id=reminder.id,
            prompt_msg_id=callback.message.message_id,
            user_id=user.id,
            telegram_user_id=reminder.telegram_user_id,
            title=reminder.title,
            schedule_type=reminder.schedule_type,
            schedule_value=reminder.schedule_value,
            send_time=reminder.send_time,
            target=reminder.target,
            target_chat_id=reminder.chat_id,
            target_thread_id=reminder.thread_id,
            target_label=target_label,
        )
        await state.set_state(AddReminder.waiting_confirmation)
        await callback.message.edit_text(
            confirm_text(reminder.title, sched, reminder.send_time, target_label),
            reply_markup=confirm_kb(),
        )


# ── /set_reminders_topic ───────────────────────────────────────────────────────

@router.message(Command("set_reminders_topic"))
async def cmd_set_reminders_topic(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    thread_id = message.message_thread_id
    if not thread_id:
        await message.answer("⚠️ Run this command inside a topic, not in the general chat.")
        return

    async with session_factory() as session:
        await GroupService.set_reminders_thread(session, message.chat.id, thread_id)

    await message.answer("✅ This topic is now set as the Reminders destination.")
