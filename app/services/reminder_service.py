import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder


class ReminderService:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        telegram_user_id: int,
        title: str,
        schedule_type: str,
        schedule_value: str | None,
        send_time: str,
        target: str,
        chat_id: int | None = None,
        thread_id: int | None = None,
    ) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            title=title,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            send_time=send_time,
            target=target,
            chat_id=chat_id,
            thread_id=thread_id,
        )
        session.add(reminder)
        await session.commit()
        await session.refresh(reminder)
        return reminder

    @staticmethod
    async def get_active(session: AsyncSession) -> list[Reminder]:
        result = await session.execute(select(Reminder).where(Reminder.is_active == True))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_user(session: AsyncSession, user_id: int) -> list[Reminder]:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id, Reminder.is_active == True)
            .order_by(Reminder.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, reminder_id: int) -> Reminder | None:
        result = await session.execute(select(Reminder).where(Reminder.id == reminder_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(session: AsyncSession, reminder_id: int) -> None:
        result = await session.execute(select(Reminder).where(Reminder.id == reminder_id))
        reminder = result.scalar_one_or_none()
        if reminder:
            await session.delete(reminder)
            await session.commit()

    @staticmethod
    async def update(
        session: AsyncSession,
        reminder_id: int,
        title: str,
        schedule_type: str,
        schedule_value: str | None,
        send_time: str,
        target: str,
        chat_id: int | None,
        thread_id: int | None,
    ) -> Reminder:
        result = await session.execute(select(Reminder).where(Reminder.id == reminder_id))
        reminder = result.scalar_one()
        reminder.title = title
        reminder.schedule_type = schedule_type
        reminder.schedule_value = schedule_value
        reminder.send_time = send_time
        reminder.target = target
        reminder.chat_id = chat_id
        reminder.thread_id = thread_id
        reminder.is_active = True
        await session.commit()
        await session.refresh(reminder)
        return reminder

    @staticmethod
    def parse_date(text: str) -> str | None:
        """Parse DD.MM.YYYY or YYYY-MM-DD → 'YYYY-MM-DD'. Returns None if invalid."""
        m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text.strip())
        if m:
            try:
                return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).strftime("%Y-%m-%d")
            except ValueError:
                pass
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text.strip())
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return None

    @staticmethod
    def parse_time(text: str) -> str | None:
        """Parse HH:MM → 'HH:MM'. Returns None if invalid."""
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", text.strip())
        if m:
            h, mm = int(m.group(1)), int(m.group(2))
            if 0 <= h < 24 and 0 <= mm < 60:
                return f"{h:02d}:{mm:02d}"
        return None
