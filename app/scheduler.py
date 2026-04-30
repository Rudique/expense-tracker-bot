from datetime import datetime

import structlog
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import get_settings
from app.models.reminder import Reminder

_settings = get_settings()
scheduler = AsyncIOScheduler(timezone=_settings.timezone)
logger = structlog.get_logger()


def _trigger(reminder: Reminder):
    tz = _settings.timezone
    hour, minute = map(int, reminder.send_time.split(":"))
    if reminder.schedule_type == "daily":
        return CronTrigger(hour=hour, minute=minute, timezone=tz)
    if reminder.schedule_type == "weekly":
        return CronTrigger(day_of_week=int(reminder.schedule_value), hour=hour, minute=minute, timezone=tz)
    if reminder.schedule_type == "monthly":
        return CronTrigger(day=int(reminder.schedule_value), hour=hour, minute=minute, timezone=tz)
    if reminder.schedule_type == "once":
        run_date = datetime.strptime(
            f"{reminder.schedule_value} {reminder.send_time}", "%Y-%m-%d %H:%M"
        )
        return DateTrigger(run_date=run_date, timezone=tz)


async def _fire(
    bot: Bot,
    chat_id: int,
    thread_id: int | None,
    title: str,
    reminder_id: int,
    session_factory: async_sessionmaker,
) -> None:
    logger.info("reminder_fired", reminder_id=reminder_id, title=title)
    try:
        await bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=f"🔔 <b>Reminder</b>\n\n{title}",
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("reminder_send_failed", reminder_id=reminder_id)

    async with session_factory() as session:
        result = await session.execute(select(Reminder).where(Reminder.id == reminder_id))
        reminder = result.scalar_one_or_none()
        if reminder and reminder.schedule_type == "once":
            reminder.is_active = False
            await session.commit()
            logger.info("reminder_deactivated", reminder_id=reminder_id)


def register_reminder(bot: Bot, session_factory: async_sessionmaker, reminder: Reminder) -> None:
    trigger = _trigger(reminder)
    if not trigger:
        return

    chat_id = reminder.telegram_user_id if reminder.target == "private" else reminder.chat_id
    thread_id = None if reminder.target == "private" else reminder.thread_id

    scheduler.add_job(
        _fire,
        trigger=trigger,
        kwargs=dict(
            bot=bot,
            chat_id=chat_id,
            thread_id=thread_id,
            title=reminder.title,
            reminder_id=reminder.id,
            session_factory=session_factory,
        ),
        id=f"reminder_{reminder.id}",
        replace_existing=True,
    )
    logger.info(
        "reminder_registered",
        reminder_id=reminder.id,
        title=reminder.title,
        schedule_type=reminder.schedule_type,
        trigger=type(trigger).__name__,
    )


def unregister_reminder(reminder_id: int) -> None:
    job_id = f"reminder_{reminder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("reminder_unregistered", reminder_id=reminder_id)


async def load_all_reminders(bot: Bot, session_factory: async_sessionmaker) -> int:
    from app.services.reminder_service import ReminderService
    async with session_factory() as session:
        reminders = await ReminderService.get_active(session)
    for reminder in reminders:
        try:
            register_reminder(bot, session_factory, reminder)
        except Exception:
            logger.exception("reminder_load_failed", reminder_id=reminder.id)
    return len(reminders)
