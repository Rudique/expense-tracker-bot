from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group


class GroupService:
    @staticmethod
    async def register_from_message(session: AsyncSession, message: Message) -> Group | None:
        if message.chat.type == ChatType.PRIVATE:
            return None
        chat_id = message.chat.id
        title = message.chat.title or f"Group {chat_id}"

        result = await session.execute(select(Group).where(Group.chat_id == chat_id))
        group = result.scalar_one_or_none()
        if group is None:
            group = Group(chat_id=chat_id, title=title)
            session.add(group)
            await session.commit()
        elif group.title != title:
            group.title = title
            await session.commit()
        return group

    @staticmethod
    async def get_all(session: AsyncSession) -> list[Group]:
        result = await session.execute(select(Group).order_by(Group.title))
        return list(result.scalars().all())

    @staticmethod
    async def get_reminders_thread(session: AsyncSession, chat_id: int) -> int | None:
        result = await session.execute(select(Group).where(Group.chat_id == chat_id))
        group = result.scalar_one_or_none()
        return group.reminders_thread_id if group else None

    @staticmethod
    async def resolve_group_target(
        session: AsyncSession, chat_id: int
    ) -> tuple[int | None, str]:
        """Returns (thread_id, target_label). thread_id is None if Reminders topic not configured."""
        result = await session.execute(select(Group).where(Group.chat_id == chat_id))
        group = result.scalar_one_or_none()
        thread_id = group.reminders_thread_id if group else None
        title = group.title if group else f"Group {chat_id}"
        return thread_id, f"📣 {title}/Reminders"

    @staticmethod
    async def set_reminders_thread(
        session: AsyncSession, chat_id: int, thread_id: int
    ) -> None:
        result = await session.execute(select(Group).where(Group.chat_id == chat_id))
        group = result.scalar_one_or_none()
        if group is None:
            group = Group(chat_id=chat_id, title=f"Group {chat_id}")
            session.add(group)
        group.reminders_thread_id = thread_id
        await session.commit()
