from sqlmodel import Session, create_engine, SQLModel
from typing import Annotated
from fastapi import Depends
from .config import get_settings

engine = create_engine(get_settings().database_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)] # канал связи с базой