from sqlmodel import select
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
import jwt
from datetime import timedelta, datetime, timezone
from .database import SessionDep
from .config import get_settings
from .models import User

password_hash = PasswordHash.recommended()

def get_password_hash(password):
    return password_hash.hash(password)

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(get_settings().access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_settings().secret_key, algorithm=get_settings().algorithm)
    return encoded_jwt

DUMMY_HASH = password_hash.hash("dummy")

def authenticate_user(session: SessionDep, username: str, password: str):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hash_password):
        return None
    return user