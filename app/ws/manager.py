from fastapi import WebSocket
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, chat_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active[chat_id].append(websocket)

    async def disconnect(self, chat_id: str, websocket: WebSocket):
        if websocket in self.active[chat_id]:
            self.active[chat_id].remove(websocket)

    async def broadcast(self, chat_id: str, message: dict):
        for ws in self.active[chat_id]:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(chat_id, ws)

manager = ConnectionManager()