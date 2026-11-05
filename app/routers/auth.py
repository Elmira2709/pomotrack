from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, Query, status, HTTPException, Depends
from typing import Annotated
from sqlmodel import select
from ..models import User, UserIn, UserOut, Token
from ..database import SessionDep
from ..security import get_password_hash, authenticate_user, create_access_token
from ..config import get_settings

router = APIRouter(prefix="/auth",
                   tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(session: SessionDep, user: UserIn):
    if session.exec(select(User).where(User.username == user.username)).first():
        raise HTTPException(status_code=409, detail="Username already registered")
    hashed = get_password_hash(user.password)
    db_auth = User.model_validate(user, update={"hash_password": hashed}) # перекладывает уже проверенные данные из одной модели в другую
    session.add(db_auth)  # запомни - надо бдет сохранить объект
    session.commit() # уже записывает
    session.refresh(db_auth) # перечитывает
    return db_auth

@router.post("/token", response_model=Token)    
def login_for_access_token(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=get_settings().access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

    