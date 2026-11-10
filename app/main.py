import os
from contextlib import asynccontextmanager

from app.database.base import Base
from app.database.session_db import engine
from app.models.ban_reason import BanReason
from app.routers import (
    admin,
    auth,
    chats,
    complaints,
    friends,
    notifications,
    posts,
    users,
)
from app.ws.manager import manager
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)


DEFAULT_BAN_REASONS = [
    "Спам",
    "Оскорбления и травля",
    "Мошенничество",
    "Неприемлемый контент",
    "Фейковый аккаунт",
]


def seed_ban_reasons() -> None:
    with Session(engine) as db:
        if db.execute(select(BanReason.id).limit(1)).first() is None:
            db.add_all([BanReason(note=note) for note in DEFAULT_BAN_REASONS])
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    seed_ban_reasons()

    task = asyncio.create_task(manager.start_listener())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)

_ = load_dotenv()
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api/static", StaticFiles(directory="app/static"), name="static")


# @app.get("/")
# def home():
#     return {"message": "Hello, World!"}


api = APIRouter(prefix="/api")

api.include_router(auth.router)
api.include_router(users.router)
api.include_router(friends.router)
api.include_router(chats.router)
api.include_router(posts.router)
api.include_router(notifications.router)
api.include_router(admin.router)
api.include_router(complaints.router)

app.include_router(api)
