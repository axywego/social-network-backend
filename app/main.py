from fastapi import FastAPI

from app.database.base import Base
from app.database.session_db import engine

from app.routers import auth, users

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, World!"}

app.include_router(auth.router)
app.include_router(users.router)