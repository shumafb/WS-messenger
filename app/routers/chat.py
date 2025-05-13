import uuid
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_async_session
from app.models.tables import Chat, Group, Message, User, chat_users, group_members
from app.schemas.tables import (
    Chat as ChatSchema,
)
from app.schemas.tables import (
    ChatCreate,
    MessageCreate,
    MessageHistoryResponse,
)
from app.schemas.tables import (
    Message as MessageSchema,
)
from app.service.connection_manager import ConnectionManager
from app.utils.jwt import get_current_user, get_current_user_ws
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("chat")

router = APIRouter(tags=["chat"])
manager = ConnectionManager()


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    token: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    current_user = await get_current_user_ws(token, session)
    logger.info(f"Пользователь {current_user.id} подключился к чату {chat_id} (WS)")
    await manager.connect(chat_id, websocket, current_user.id)
    try:
        while True:
            try:
                data = await websocket.receive_json()
                logger.debug(f"WS получены данные от пользователя {current_user.id}: {data}")
            except JSONDecodeError:
                continue
            event_type = data.get("type")
            if event_type == "message":
                client_msg_id = data.get("client_message_id")
                text = data.get("text")
                logger.info(f"Пользователь {current_user.id} отправляет сообщение в чат {chat_id}: {text}")
                msg = Message(
                    chat_id=chat_id,
                    sender_id=current_user.id,
                    text=text,
                    timestamp=datetime.utcnow(),
                    client_message_id=str(uuid.uuid4()),
                )
                session.add(msg)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    continue
                await session.refresh(msg)
                payload = {
                    "type": "message",
                    "id": msg.id,
                    "chat_id": chat_id,
                    "sender_id": current_user.id,
                    "text": text,
                    "timestamp": msg.timestamp.isoformat(),
                }
                await manager.broadcast(chat_id, payload)
                logger.info(f"Сообщение отправлено всем в чате {chat_id}: id {msg.id}")
            elif event_type == "read":
                msg_id = data.get("message_id")
                result = await session.execute(select(Message).filter_by(id=msg_id))
                msg = result.scalar_one_or_none()
                if msg and not msg.is_read:
                    logger.info(f"Пользователь {current_user.id} отметил сообщение {msg_id} как прочитанное в чате {chat_id}")
                    msg.is_read = True
                    try:
                        await session.commit()
                    except IntegrityError:
                        await session.rollback()
                    payload = {
                        "type": "read",
                        "message_id": msg_id,
                        "reader_id": current_user.id,
                    }
                    await manager.send_personal_message(chat_id, msg.sender_id, payload)
    except WebSocketDisconnect:
        manager.disconnect(chat_id, websocket)
        logger.info(f"Пользователь {current_user.id} отключился от чата {chat_id} (WS)")


@router.post("/chats", response_model=ChatSchema)
async def create_chat(
    data: ChatCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    logger.info(f"Запрос на создание чата от пользователя {current_user.id}: тип={data.chat_type}, название={data.name}, участники={data.member_ids}")
    if data.chat_type == "private":
        if len(data.member_ids) != 1:
            raise HTTPException(
                status_code=400,
                detail="При создании приватного чата можно указать только одного участника",
            )
        if current_user.id in data.member_ids:
            raise HTTPException(
                status_code=400,
                detail="Нельзя создать приватный чат с самим собой",
            )

        existing_chat = await session.execute(
            select(Chat)
            .join(chat_users, Chat.id == chat_users.c.chat_id)
            .where(
                Chat.chat_type == "private",
                chat_users.c.user_id.in_([current_user.id, data.member_ids[0]]),
            )
            .group_by(Chat.id)
            .having(func.count(chat_users.c.user_id) == 2)
        )
        if existing_chat.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Приватный чат между этими пользователями уже существует",
            )
    chat = Chat(
        name=data.name,
        chat_type=data.chat_type,
    )
    session.add(chat)
    await session.flush()

    unique_ids = set(data.member_ids + [current_user.id])
    if unique_ids:
        rows = [{"chat_id": chat.id, "user_id": uid} for uid in unique_ids]
        await session.execute(insert(chat_users), rows)

    if data.chat_type == "group":
        group = Group(chat_id=chat.id, name=data.name, creator_id=current_user.id)
        session.add(group)
        await session.flush()
        if unique_ids:
            rows = [{"group_id": group.id, "user_id": uid} for uid in unique_ids]
            await session.execute(insert(group_members), rows)

    await session.commit()
    result = await session.execute(
        select(Chat).options(selectinload(Chat.members)).filter_by(id=chat.id)
    )
    chat_with_members = result.scalar_one()
    return chat_with_members


@router.get("/chats", response_model=List[ChatSchema])
async def list_chats(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    logger.info(f"Запрос списка чатов для пользователя {current_user.id}")
    q = select(Chat).join(chat_users).filter(chat_users.c.user_id == current_user.id)
    result = await session.execute(q)
    return result.scalars().all()


@router.get("/chats/{chat_id}/messages", response_model=List[MessageSchema])
async def get_history(
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    logger.info(f"Получение истории чата {chat_id} пользователем {current_user.id}")
    q = select(Message).filter_by(chat_id=chat_id).order_by(Message.timestamp)
    result = await session.execute(q)
    return result.scalars().all()


@router.post("/chats/{chat_id}/messages", response_model=MessageSchema)
async def send_message_http(
    chat_id: int,
    data: MessageCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    logger.info(f"HTTP: отправка сообщения пользователем {current_user.id} в чат {chat_id}: {data.text}")
    msg = Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        text=data.text,
        timestamp=datetime.utcnow(),
        client_message_id=str(uuid.uuid4()),
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


@router.get("/history/{chat_id}", response_model=MessageHistoryResponse)
async def get_message_history(
    chat_id: int,
    limit: int = Query(
        default=50, ge=1, le=100, description="Количество сообщений на странице"
    ),
    offset: int = Query(default=0, ge=0, description="Смещение от начала"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"HTTP: получение истории сообщений чата {chat_id}, смещение={offset}, лимит={limit}, пользователь={current_user.id}")
    chat_member = await session.execute(
        select(chat_users).where(
            chat_users.c.chat_id == chat_id, chat_users.c.user_id == current_user.id
        )
    )
    if not chat_member.first():
        raise HTTPException(status_code=403, detail="У вас нет доступа к этому чату")

    total_count = await session.execute(
        select(func.count(Message.id)).filter(Message.chat_id == chat_id)
    )
    total = total_count.scalar()

    messages = await session.execute(
        select(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.timestamp.asc())
        .offset(offset)
        .limit(limit)
    )

    return MessageHistoryResponse(
        items=messages.scalars().all(), total=total, offset=offset, limit=limit
    )
