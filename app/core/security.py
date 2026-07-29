from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv
import os
import secrets
import hashlib

load_dotenv()

SECRET_KEY = os.getenv("SECRET_JWT_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token() -> tuple[str, str, datetime]:
    raw_token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return raw_token, token_hash, expires_at