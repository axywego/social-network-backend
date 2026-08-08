from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.base import Base
from app.database.session_db import engine

from app.routers import auth, users, friends, chats, posts

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def home():
    return {"message": "Hello, World!"}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(friends.router)
app.include_router(chats.router)
app.include_router(posts.router)