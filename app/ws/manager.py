import asyncio
import json
import logging
import os
from collections import defaultdict
from termios import VINTR
from typing import Iterable

import redis.asyncio as redis
from app.core.utils import get_friends
from fastapi import WebSocket
from sqlalchemy.orm import Session

PRESENCE_TTL = 30
HEARTBEAT_INTERVAL = 15

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.active_chats: dict[str, set[WebSocket]] = defaultdict(set)
        self.active_users: dict[str, WebSocket] = {}
        self.chat_viewers: dict[str, set[str]] = defaultdict(set)
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
                    await self._local_broadcast_to_chat(
                        data["chat_id"], data["message"]
                    )
                elif msg["channel"] == "presence_broadcast":
                    await self._local_send_to_users(data["user_ids"], data["message"])
            except Exception:
                logger.exception("Ошибка обработки сообщения из redis pub/sub")

    # chats

    async def connect_to_chat(self, chat_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_chats[chat_id].add(websocket)
        self.chat_viewers[chat_id].add(user_id)

    async def disconnect_from_chat(
        self, chat_id: str, user_id: str, websocket: WebSocket
    ):
        connections = self.active_chats.get(chat_id)
        if connections:
            connections.discard(websocket)
            if not connections:
                del self.active_chats[chat_id]
        viewers = self.chat_viewers.get(chat_id)
        if viewers:
            viewers.discard(user_id)
            if not viewers:
                del self.chat_viewers[chat_id]

    async def broadcast_to_chat(self, chat_id: str, message: dict):
        _ = await self.redis.publish(
            "chat_broadcast", json.dumps({"chat_id": chat_id, "message": message})
        )

    async def _local_broadcast_to_chat(self, chat_id: str, message: dict):
        for ws in list(self.active_chats.get(chat_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect_from_chat(chat_id, ws)

    async def users_not_in_chat(self, user_ids: list[str], chat_id: str) -> list[str]:
        viewers = self.chat_viewers.get(chat_id, set())
        return [user_id for user_id in user_ids if user_id not in viewers]

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

        await self._mark_online(user_id)

        self._heartbeat_tasks[user_id] = asyncio.create_task(
            self._heartbeat_loop(user_id)
        )

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

        _ = await self.redis.delete(f"presence:{user_id}")
        _ = await self.redis.srem("online_users", user_id)  # добавить эту строку
        return True

    async def disconnect_from_users(self, user_id: str, sess: Session):
        went_offline = await self._drop_local_connection(user_id)
        if went_offline:
            await self.broadcast_presence(user_id, is_online=False, sess=sess)

    async def send_to_user(self, user_id: str, message: dict):
        _ = await self.redis.publish(
            "presence_broadcast",
            json.dumps({"user_ids": [user_id], "message": message}),
        )

    async def send_to_users(self, user_ids: Iterable[str], message: dict):
        unique_user_ids = [user_id for user_id in user_ids]
        if not unique_user_ids:
            return

        _ = await self.redis.publish(
            "presence_broadcast",
            json.dumps({"user_ids": unique_user_ids, "message": message}),
        )

    async def _local_send_to_users(self, user_ids: Iterable[str], message: dict):
        for user_id in user_ids:
            conn = self.active_users.get(user_id)
            if not conn:
                continue

            try:
                await conn.send_json(message)
            except Exception:
                await self._drop_local_connection(user_id)


manager = ConnectionManager(redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"))
