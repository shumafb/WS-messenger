from typing import List

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import Message, group_members


class ChatService:
    @staticmethod
    async def send_message(
        chat_id: int,
        user_id: int,
        text: str,
        client_message_id: str,
        session: AsyncSession,
    ) -> Message:
        membership_stmt = select(group_members).where(
            group_members.c.group_id == chat_id, group_members.c.user_id == user_id
        )
        membership = await session.execute(membership_stmt)
        if not membership.first():
            raise HTTPException(
                status_code=403, detail="Пользователь не является участником этого чата"
            )

        msg = Message(
            chat_id=chat_id,
            sender_id=user_id,
            text=text,
            client_message_id=client_message_id,
        )
        session.add(msg)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            existing = await session.execute(
                select(Message).where(Message.client_message_id == client_message_id)
            )
            return existing.scalar_one()
        await session.refresh(msg)
        return msg

    @staticmethod
    async def mark_read(
        chat_id: int,
        user_id: int,
        message_id: int,
        session: AsyncSession,
    ) -> List[int]:
        membership_stmt = select(group_members).where(
            group_members.c.group_id == chat_id, group_members.c.user_id == user_id
        )
        membership = await session.execute(membership_stmt)
        if not membership.first():
            raise HTTPException(
                status_code=403, detail="Пользователь не является участником этого чата"
            )

        update_stmt = (
            update(Message).where(Message.id == message_id).values(is_read=True)
        )
        await session.execute(update_stmt)
        await session.commit()

        original = await session.get(Message, message_id)
        return [original.sender_id]

    @staticmethod
    async def get_history(
        chat_id: int,
        user_id: int,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Message]:
        membership_stmt = select(group_members).where(
            group_members.c.group_id == chat_id, group_members.c.user_id == user_id
        )
        membership = await session.execute(membership_stmt)
        if not membership.first():
            raise HTTPException(
                status_code=403, detail="Пользователь не является участником этого чата"
            )

        q = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(q)
        return result.scalars().all()
