import asyncio
from typing import List, Optional
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}
        self.user_connections: Dict[int, List[WebSocket]] = {}

        self._lock = asyncio.Lock()

    async def connect(self, chat_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            connections = self.active_connections.setdefault(chat_id, [])
            connections.append(websocket)
            self.user_connections.setdefault(user_id, []).append(websocket)

    async def disconnect(self, chat_id: int, user_id: int, websocket: WebSocket):

        async with self._lock:
            connections = self.active_connections.get(chat_id)
            if not connections:
                return
            if websocket in connections:
                connections.remove(websocket)
            if not connections:
                self.active_connections.pop(chat_id, None)
            user_conns = self.user_connections.get(user_id)
            if user_conns and websocket in user_conns:
                user_conns.remove(websocket)
                if not user_conns:
                    self.user_connections.pop(user_id, None)
    
    async def broadcast(self, chat_id: int, message: dict):

        connections = self.active_connections.get(chat_id, [])
        for connection in connections:
            await connection.send_json(message)

    async def send_message(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)

    async def send_personal_by_user(self, user_id: int, message: dict):
        for ws in self.user_connections.get(user_id, []):
            await ws.send_json(message)

manager = ConnectionManager()