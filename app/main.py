from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.base import Base
from app.database.session_db import engine

from app.routers import auth, users, friends, chats, posts

import os
from dotenv import load_dotenv

Base.metadata.create_all(bind=engine)

app = FastAPI()

load_dotenv()
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

app.include_router(api)