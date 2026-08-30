import os
from contextlib import asynccontextmanager

from app.database.base import Base
from app.database.session_db import engine
from app.routers import auth, chats, friends, notifications, posts, users
from app.ws.manager import manager
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

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


@app.get("/")
def home():
    return {"message": "Hello, World!"}


api = APIRouter(prefix="/api")

api.include_router(auth.router)
api.include_router(users.router)
api.include_router(friends.router)
api.include_router(chats.router)
api.include_router(posts.router)
api.include_router(notifications.router)

app.include_router(api)
