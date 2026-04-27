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
