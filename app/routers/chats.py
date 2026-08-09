from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session_db import get_db
from app.models.user import User
from app.models.chat import Chat
from app.models.chat_user import ChatUser
from app.models.chat_message import ChatMessage

from app.schemes.chats import ChatCreate, ChatPreview, MessageCreate, MessageOut

from app.core.dependencies import get_current_user

from app.core.utils import get_ordered_pair

import os

import uuid

import datetime

CHAT_IMAGES_URL = "app/static/private_storage/chat_images"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024

router = APIRouter(prefix="/chats", tags=["chats"])

def build_image_url(chat_id: uuid.UUID, filename: str | None) -> str | None:
    return f"/chats/{chat_id}/images/{filename}" if filename else None

def is_membership(db: Session, chat_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return (
        db.query(ChatUser)
        .filter(ChatUser.chat_id == chat_id, ChatUser.user_id == user_id, ChatUser.left_at.is_(None))
        .first() is not None
    )

@router.post("/{chat_id}/images")
async def upload_chat_image(
    chat_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_membership(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not a member of this chat")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    filename = f"{uuid.uuid4()}{ext}"
    chat_dir = os.path.join(CHAT_IMAGES_URL, str(chat_id))
    os.makedirs(chat_dir, exist_ok=True)

    filepath = os.path.join(chat_dir, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    return {"filename": filename}

@router.get("/{chat_id}/images/{filename}")
def get_chat_image(
    chat_id: uuid.UUID,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_membership(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not a member of this chat")

    filename = os.path.basename(filename)
    filepath = os.path.join(CHAT_IMAGES_URL, str(chat_id), filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(filepath)

@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def get_messages_from_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_membership(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not a member of this chat")

    finded_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        MessageOut(
            sender_id=m.user_id,
            content=m.content,
            image_url=build_image_url(chat_id, m.image_url),
            created_at=m.created_at
        )
        for m in finded_messages
    ]


@router.post("/{chat_id}/messages", response_model=MessageOut)
def send_message(
    chat_id: uuid.UUID,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_membership(db, chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not a member of this chat")

    message = ChatMessage(
        chat_id=chat_id,
        user_id=current_user.id,
        content=payload.content,
        image_url=payload.image_url
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return MessageOut(
        sender_id=message.user_id,
        content=message.content,
        image_url=build_image_url(chat_id, message.image_url),
        created_at=message.created_at
    )

@router.get("/{user_id}", response_model=ChatPreview)
def get_direct_chat(user_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    min_id, max_id = get_ordered_pair(user_id, current_user.id)
    chat = db.query(Chat).filter(Chat.user_a_id == min_id, Chat.user_b_id == max_id).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    other_user = db.query(User).filter(User.id == user_id).first()

    return ChatPreview(
        chat_id=chat.id,
        name=f"{other_user.first_name} {other_user.last_name}",
        last_message=None,
        last_message_time=None
    )

@router.post("/create_chat", response_model=ChatPreview)
def create_chat(payload: ChatCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.type == "direct":
        if payload.user_if_direct == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot create a chat with yourself")

        other_user = db.query(User).filter(User.id == payload.user_if_direct).first()
        if not other_user:
            raise HTTPException(status_code=400, detail="Cannot find user")

        min_id, max_id = get_ordered_pair(current_user.id, payload.user_if_direct)

        existing_chat = db.query(Chat).filter(Chat.type == "direct", Chat.user_a_id == min_id, Chat.user_b_id == max_id).first()

        if existing_chat:
            raise HTTPException(status_code=400, detail="Chat already exists")

        new_chat = Chat(
            type="direct",
            user_a_id=min_id,
            user_b_id=max_id,
        )
        db.add(new_chat)
        db.flush()

        db.add_all([
            ChatUser(chat_id=new_chat.id, user_id=current_user.id),
            ChatUser(chat_id=new_chat.id, user_id=other_user.id)
        ])

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Chat already exists")

        db.refresh(new_chat)

        return ChatPreview(
            chat_id=new_chat.id,
            name=f"{other_user.first_name} {other_user.last_name}",
            last_message=None,
            last_message_time=None
        )

    elif payload.type == "group":
        new_chat = Chat(
            type="group",
            name=payload.name
        )
        db.add(new_chat)
        db.flush()

        db.add(ChatUser(chat_id=new_chat.id, user_id=current_user.id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Failed to create chat")

        db.refresh(new_chat)

        return ChatPreview(
            chat_id=new_chat.id,
            name=new_chat.name,
            last_message=None,
            last_message_time=None
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid chat type")

@router.get("", response_model=list[ChatPreview])
def get_all_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    previews = list()

    direct_chats = db.query(Chat).filter(Chat.type == "direct", or_(Chat.user_a_id == current_user.id, Chat.user_b_id == current_user.id)).all()
    for chat in direct_chats:
        other_user_id = chat.user_b_id if chat.user_a_id == current_user.id else chat.user_a_id
        other_user = db.query(User).filter(User.id == other_user_id).first()

        last_message = db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).order_by(ChatMessage.created_at.desc()).first()

        previews.append(ChatPreview(
            chat_id=chat.id,
            name=f"{other_user.first_name} {other_user.last_name}" if other_user else "Unknown",
            last_message=(last_message.content if last_message.content is not None else "Image") if last_message else None,
            last_message_time=last_message.created_at if last_message else None,
            avatar_url=other_user.avatar_url
        ))

    group_chats = (
        db.query(Chat)
        .join(ChatUser, ChatUser.chat_id == Chat.id)
        .filter(Chat.type == "group", ChatUser.user_id == current_user.id)
        .all()
    )
    for chat in group_chats:
        last_message = db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).order_by(ChatMessage.created_at.desc()).first()

        previews.append(ChatPreview(
            chat_id=chat.id,
            name=chat.name,
            last_message=(last_message.content if last_message.content is not None else "Image") if last_message else None,
            last_message_time=last_message.created_at if last_message else None,
            avatar_url=chat.avatar_url
        ))

    previews.sort(key=lambda p: p.last_message_time or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)

    return previews