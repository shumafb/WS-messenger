from typing import Dict, List, Tuple

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[Tuple[WebSocket, int]]] = {}

    async def connect(self, chat_id: int, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []

        if not any(
            ws is websocket and uid == user_id
            for ws, uid in self.active_connections[chat_id]
        ):
            self.active_connections[chat_id].append((websocket, user_id))

    async def disconnect(
        self, chat_id: int, websocket: WebSocket, user_id: int
    ) -> None:
        if chat_id in self.active_connections:
            self.active_connections[chat_id] = [
                (ws, uid)
                for ws, uid in self.active_connections[chat_id]
                if not (ws is websocket and uid == user_id)
            ]
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def broadcast(self, chat_id: int, message: dict) -> None:
        if chat_id in self.active_connections:
            for websocket, _ in list(self.active_connections[chat_id]):
                try:
                    await websocket.send_json(message)
                except Exception:
                    await self.disconnect(chat_id, websocket, _)

    async def send_personal_message(
        self, chat_id: int, user_id: int, message: dict
    ) -> None:
        if chat_id in self.active_connections:
            for websocket, uid in self.active_connections[chat_id]:
                if uid == user_id:
                    try:
                        await websocket.send_json(message)
                    except Exception:
                        pass
