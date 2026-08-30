from app.core.dependencies import get_user_from_token
from app.database.session_db import get_db
from app.ws.manager import manager
from fastapi import (
    APIRouter,
    Depends,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/notifications")


@router.websocket("/ws")
async def notifications_websocket(
    websocket: WebSocket, token: str = Query(...), db: Session = Depends(get_db)
):
    user = get_user_from_token(token, db)
    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect_to_users(str(user.id), websocket, db)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_from_users(str(user.id), db)
