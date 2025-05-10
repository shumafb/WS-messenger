from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db, get_current_user_ws
from ..service.connection_manager import manager as connection_manager
from ..service.chat_service import ChatService

router = APIRouter(
    tags=["chat"],
)

@router.websocket("/ws/{chat_id}")
async def chat_ws(
    websocket: WebSocket,
    chat_id: int,
    token: str,
    session: AsyncSession = Depends(get_db),
):
    try:
        user = await get_current_user_ws(token, session)
    except:
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
                    session=session
                ) 
                await connection_manager.broadcast(chat_id, {
                    "type": "message",
                    "message_id": msg.id,
                    "sender_id": msg.sender_id,
                    "text": msg.text,
                    "timestamp": msg.timestamp.isoformat(),
                    "client_message_id": payload["client_message_id"],
                })
            elif payload.get("type") == "read":
                targets = await ChatService.mark_read(
                    chat_id=chat_id,
                    user_id=user.id,
                    message_id=payload["message_id"],
                    session=session
                )
                for target_user_id in targets:
                    await connection_manager.send_personal_by_user(target_user_id, {
                        "type": "read",
                        "message_id": payload["message_id"],
                    })