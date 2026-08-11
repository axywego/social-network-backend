from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session_db import get_db
from app.models.user import User
from app.models.chat import Chat
from app.models.chat_user import ChatUser
from app.models.chat_message import ChatMessage

from app.schemes.chats import ChatCreate, ChatPreview, MessageCreate, MessageOut, AddRemoveUserFromChat
from app.schemes.users import UserOut

from typing import Optional

from app.core.dependencies import get_current_user, get_user_from_token
from app.core.utils import get_ordered_pair, compress_message, decompress_message

from app.ws.manager import manager

import os

import uuid

from datetime import datetime, timezone

router = APIRouter(prefix="/notifications")

@router.websocket("/ws")
async def notifications_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    user = get_user_from_token(token, db)
    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect_to_users(str(user.id), websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_from_users(str(user.id), websocket)