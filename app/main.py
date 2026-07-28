from fastapi import FastAPI

from app.database.base import Base
from app.database.session_db import engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, World!"}