from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
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

from app.core.dependencies import get_current_user
from app.core.utils import get_ordered_pair, compress_message, decompress_message

from app.ws.manager import manager

import os

import uuid

from datetime import datetime, timezone

router = APIRouter(prefix="/notifications")