from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..models.tables import Chat, User
from ..dependencies import get_async_session, get_current_user
from ..schemas.tables import Chat as ChatRead 

router = APIRouter(prefix="/chats", tags=["chats"])

class ChatCreate(BaseModel):
    name: str
    is_group: bool = True
    user_ids: List[int]

class ParticipantsUpdate(BaseModel):
    user_ids: List[int]

@router.post("/", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
async def create_chat(
    data: ChatCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user)
):
    # Создаём чат (групповой или личный)
    chat = Chat(name=data.name if data.is_group else None, is_group=data.is_group)
    db.add(chat)
    await db.flush()  # получить chat.id

    # Собираем участников: текущий пользователь + указанные
    user_set = set(data.user_ids) | {current_user.id}
    for uid in user_set:
        db.add(User(chat_id=chat.id, user_id=uid))

    await db.commit()
    await db.refresh(chat)
    return ChatRead.from_orm(chat)

@router.post("/{chat_id}/participants", status_code=status.HTTP_204_NO_CONTENT)
async def add_participants(
    chat_id: int,
    data: ParticipantsUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user)
):
    # Проверка: чат существует и текущий пользователь - участник
    chat = await db.get(Chat, chat_id)
    if not chat or not chat.is_group:
        raise HTTPException(status_code=404, detail="Групповой чат не найден")

    result = await db.execute(
        select(User).where(User.chat_id == chat_id, User.user_id == current_user.id)
    )
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Нет доступа к чату")

    # Добавляем новых участников
    for uid in set(data.user_ids):
        exists = await db.execute(
            select(User).where(User.chat_id == chat_id, User.user_id == uid)
        )
        if not exists.scalars().first():
            db.add(User(chat_id=chat_id, user_id=uid))
    await db.commit()

@router.delete("/{chat_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_participant(
    chat_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user)
):
    # Проверка: чат существует и текущий пользователь - участник
    chat = await db.get(Chat, chat_id)
    if not chat or not chat.is_group:
        raise HTTPException(status_code=404, detail="Групповой чат не найден")

    result = await db.execute(
        select(User).where(User.chat_id == chat_id, User.user_id == current_user.id)
    )
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Нет доступа к чату")

    # Удаляем участника
    await db.execute(
        delete(User).where(User.chat_id == chat_id, User.user_id == user_id)
    )
    await db.commit()
