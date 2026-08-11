from fastapi import WebSocket
from collections import defaultdict
from typing import Iterable

class ConnectionManager:
    def __init__(self):
        self.active_chats: dict[str, set[WebSocket]] = defaultdict(list)
        self.active_users: dict[str, set[WebSocket]] = defaultdict(list)

    # chats

    async def connect_to_chat(self, chat_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_chats[chat_id].add(websocket)

    async def disconnect_from_chat(self, chat_id: str, websocket: WebSocket):
        connections = self.active_chats.get(chat_id)
        if not connections:
            return

        connections.discard(websocket)

        if not connections:
            del self.active_chats[chat_id]

    async def broadcast_to_chat(self, chat_id: str, message: dict):
        for ws in list(self.active_chats.get(chat_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect_from_chat(chat_id, ws)

    # users

    async def connect_to_user(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_users[user_id].add(websocket)

    async def disconnect_from_user(self, user_id: str, websocket: WebSocket):
        connections = self.active_users.get(user_id)
        if not connections:
            return

        connections.discard(websocket)

        if not connections:
            del self.active_users[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        for ws in list(self.active_users.get(user_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect_from_user(user_id, ws)

    async def send_to_users(self, user_ids: Iterable[str], message: dict):
        unique_user_ids = {user_id for user_id in user_ids}

        for user_id in unique_user_ids:
            await self.send_to_user(user_id, message)

manager = ConnectionManager()