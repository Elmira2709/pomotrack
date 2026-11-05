from fastapi import APIRouter, Query, HTTPException, Path
from typing import Annotated
from sqlmodel import select
from datetime import timedelta, timezone
from ..models import SesAnswer, PomodoroSession, SesFilters, SesCreate
from ..database import SessionDep


router = APIRouter(prefix="/sessions",
                   tags=["sessions"])

@router.post("/", response_model=SesAnswer, status_code=201)
def create_ses(session: SessionDep, ses: SesCreate):
    db_ses = PomodoroSession.model_validate(ses) # создаёт объект модели из данных, попутно проверяя их
    session.add(db_ses)
    session.commit()
    session.refresh(db_ses)
    return db_ses

@router.get("/", response_model=list[SesAnswer])
def get_list_sessions(filters: Annotated[SesFilters, Query()], session: SessionDep):
    query = select(PomodoroSession)
    if filters.type is not None:
        query = query.where(filters.type == PomodoroSession.type)
    if filters.task_id is not None:
        query = query.where(filters.task_id == PomodoroSession.task_id)
    if filters.date_from is not None:
        query = query.where(filters.date_from.combine(timezone.utc) <= PomodoroSession.started_at)    
    if filters.date_to is not None:
        query = query.where(filters.date_to.combine(timezone.utc) + timedelta(days=1) > PomodoroSession.started_at)
    res = session.exec(query.order_by(PomodoroSession.started_at.desc()).offset(filters.skip).limit(filters.limit)).all()    
    return res

@router.delete("/{session_id}", status_code=204)
def delete_session(session: SessionDep, session_id: Annotated[int, Path(gt=0)]):
    res = session.get(PomodoroSession, session_id)
    if res:
        session.delete(res)
        session.commit()
        return
    raise HTTPException(status_code=404, detail="Session not found")