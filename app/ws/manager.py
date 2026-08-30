import json
import logging
from collections import defaultdict
from typing import Iterable

from fastapi import WebSocket
import redis.asyncio as redis
from sqlalchemy.orm import Session

from app.core.utils import get_friends

import asyncio

PRESENCE_TTL = 30
HEARTBEAT_INTERVAL = 15

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.active_chats: dict[str, set[WebSocket]] = defaultdict(set)
        self.active_users: dict[str, WebSocket] = {}
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}

        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis.pubsub()

    async def start_listener(self):
        await self.pubsub.subscribe("chat_broadcast", "presence_broadcast")
        async for msg in self.pubsub.listen():
            if msg["type"] != "message":
                continue
            try:
                data = json.loads(msg["data"])
                if msg["channel"] == "chat_broadcast":
                    await self._local_broadcast_to_chat(data["chat_id"], data["message"])
                elif msg["channel"] == "presence_broadcast":
                    await self._local_send_to_users(data["user_ids"], data["message"])
            except Exception:
                logger.exception("Ошибка обработки сообщения из redis pub/sub")
                
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
        await self.redis.publish(
            "chat_broadcast",
            json.dumps({"chat_id": chat_id, "message": message})
        )

    async def _local_broadcast_to_chat(self, chat_id: str, message: dict):
        for ws in list(self.active_chats.get(chat_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect_from_chat(chat_id, ws)

    # users / presence

    async def _is_online(self, user_id: str) -> bool:
        return await self.redis.exists(f"presence:{user_id}") == 1

    async def _mark_online(self, user_id: str):
        await self.redis.set(f"presence:{user_id}", "1", ex=PRESENCE_TTL)

    async def _heartbeat_loop(self, user_id: str):
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await self._mark_online(user_id)
        except asyncio.CancelledError:
            pass

    async def broadcast_presence(self, user_id: str, is_online: bool, sess: Session):
        friends = get_friends(user_id, sess)
        online_now = [user for user in self.active_users if user in friends]
        message = {"type": "presence", "user_id": user_id, "online": is_online}
        await self.send_to_users(online_now, message)

    async def connect_to_users(self, user_id: str, websocket: WebSocket, sess: Session):
        await websocket.accept()

        was_offline = await self.redis.sadd("online_users", user_id) == 1
        self.active_users[user_id] = websocket

        self._heartbeat_tasks[user_id] = asyncio.create_task(self._heartbeat_loop(user_id))

        friends = get_friends(user_id, sess)
        online_now = []
        if friends:
            pipe = self.redis.pipeline()
            for fid in friends:
                pipe.exists(f"presence:{fid}")
            flags = await pipe.execute()
            online_now = [uid for uid, is_on in zip(friends, flags) if is_on]

        await websocket.send_json({"type": "presence_snapshot", "online": online_now})

        if was_offline:
            await self.broadcast_presence(user_id, is_online=True, sess=sess)


    async def _drop_local_connection(self, user_id: str) -> bool:
        conn = self.active_users.get(user_id)
        if not conn:
            return False

        del self.active_users[user_id]

        task = self._heartbeat_tasks.pop(user_id, None)
        if task:
            task.cancel()

        await self.redis.delete(f"presence:{user_id}")
        return True

    async def disconnect_from_users(self, user_id: str, sess: Session):
        went_offline = await self._drop_local_connection(user_id)
        if went_offline:
            await self.broadcast_presence(user_id, is_online=False, sess=sess)

    async def send_to_user(self, user_id: str, message: dict):
        await self.redis.publish("presence_broadcast", json.dumps({"user_ids": [user_id], "message": message}))

    async def send_to_users(self, user_ids: Iterable[str], message: dict):
        unique_user_ids = [user_id for user_id in user_ids]
        if not unique_user_ids:
            return
        
        await self.redis.publish("presence_broadcast", json.dumps({"user_ids": unique_user_ids, "message": message}))

    async def _local_send_to_users(self, user_ids: Iterable[str], message: dict):
        for user_id in user_ids:
            conn = self.active_users.get(user_id)
            if not conn:
                continue

            try:
                await conn.send_json(message)
            except Exception:
                await self._drop_local_connection(user_id)
        
manager = ConnectionManager()