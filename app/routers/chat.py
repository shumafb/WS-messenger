from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..schemas.tables import MessageResponse
from ..service.chat_service import ChatService
from ..service.connection_manager import manager as connection_manager
from ..utils.jwt import get_current_user_ws

router = APIRouter(
    tags=["chat"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@router.websocket("/ws/{chat_id}")
async def chat_ws(
    websocket: WebSocket,
    chat_id: int,
    token: str,
    session: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user_ws(token, session)
    except WebSocketDisconnect:
        return await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

    await connection_manager.connect(chat_id, user.id, websocket)

    try:
        while True:
            payload = await websocket.receive_json()

            if payload.get("type") == "message":
                msg = await ChatService.send_message(
                    chat_id=chat_id,
                    user_id=user.id,
                    text=payload["text"],
                    client_message_id=payload["client_message_id"],
                    session=session,
                )
                await connection_manager.broadcast(
                    chat_id,
                    {
                        "type": "message",
                        "message_id": msg.id,
                        "sender_id": msg.sender_id,
                        "text": msg.text,
                        "timestamp": msg.timestamp.isoformat(),
                        "client_message_id": payload["client_message_id"],
                    },
                )
            elif payload.get("type") == "read":
                targets = await ChatService.mark_read(
                    chat_id=chat_id,
                    user_id=user.id,
                    message_id=payload["message_id"],
                    session=session,
                )
                for target_user_id in targets:
                    await connection_manager.send_personal_by_user(
                        target_user_id,
                        {
                            "type": "read",
                            "message_id": payload["message_id"],
                        },
                    )
    except WebSocketDisconnect:
        await connection_manager.disconnect(chat_id, user.id, websocket)


@router.get("/history/{chat_id}", response_model=list[MessageResponse])
async def http_get_history(
    chat_id: int,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    user = await get_current_user_ws(token, session)

    messages = await ChatService.get_history(chat_id, user.id, session, limit, offset)
    return [
        MessageResponse(
            message_id=m.id,
            sender_id=m.sender_id,
            text=m.text,
            timestamp=m.timestamp.isoformat(),
            is_read=m.is_read,
            client_message_id=m.client_message_id,
        )
        for m in messages
    ]


@router.post("/chats/{chat_id}/messages/{message_id}/read")
async def http_mark_read(
    chat_id: int,
    message_id: int,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
):
    user = await get_current_user_ws(token, session)

    targets = await ChatService.mark_read(chat_id, user.id, message_id, session)
    for target_user_id in targets:
        await connection_manager.send_personal_by_user(
            target_user_id,
            {
                "type": "read",
                "message_id": message_id,
            },
        )
    return {"status": "ok"}
