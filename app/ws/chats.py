from fastapi import WebSocket, WebSocketDisconnect, Query, Depends
from app.routers.chats import router, is_membership
import uuid

from sqlalchemy.orm import Session

from app.core.dependencies import get_user_from_token

from app.ws.manager import manager

from app.database.session_db import get_db

@router.websocket("/ws/{chat_id}")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: uuid.UUID,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    user = get_user_from_token(token, db)
    if not user or not is_membership(db, chat_id, user.id):
        await websocket.close(code=1008)
        return

    await manager.connect_to_chat(str(chat_id), websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_from_chat(str(chat_id), websocket)
