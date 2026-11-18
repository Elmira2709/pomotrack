from fastapi import APIRouter, Query, HTTPException, Path, Depends
from typing import Annotated
from sqlmodel import select
from datetime import datetime, time, timedelta, timezone
from ..models import SesAnswer, PomodoroSession, SesFilters, SesCreate
from ..database import SessionDep
from ..dependencies import find_task, CurrentUser, get_current_user

router = APIRouter(prefix="/sessions",
                   tags=["sessions"],
                   dependencies=[Depends(get_current_user)])

@router.post("/", response_model=SesAnswer, status_code=201)
def create_ses(session: SessionDep, ses: SesCreate, current_user: CurrentUser):
    if ses.task_id is not None:
        find_task(session, current_user, ses.task_id)
    db_ses = PomodoroSession.model_validate(ses, update={"user_id": current_user.id})
    session.add(db_ses)
    session.commit()
    session.refresh(db_ses)
    return db_ses

@router.get("/", response_model=list[SesAnswer])
def get_list_sessions(filters: Annotated[SesFilters, Query()], session: SessionDep, current_user: CurrentUser):
    query = select(PomodoroSession).where(PomodoroSession.user_id == current_user.id)
    if filters.type is not None:
        query = query.where(filters.type == PomodoroSession.type)
    if filters.task_id is not None:
        query = query.where(filters.task_id == PomodoroSession.task_id)
    if filters.date_from is not None:
        start = datetime.combine(filters.date_from, time.min, tzinfo=timezone.utc)
        query = query.where(start <= PomodoroSession.started_at)
    if filters.date_to is not None:
        end = datetime.combine(filters.date_to, time.min, tzinfo=timezone.utc) + timedelta(days=1)
        query = query.where(end > PomodoroSession.started_at)
    return session.exec(
        query.order_by(PomodoroSession.started_at.desc()).offset(filters.skip).limit(filters.limit)
    ).all()

@router.delete("/{session_id}", status_code=204)
def delete_session(session: SessionDep, current_user: CurrentUser,
                   session_id: Annotated[int, Path(gt=0)]):
    res = session.exec(select(PomodoroSession).where(
        PomodoroSession.id == session_id,
        PomodoroSession.user_id == current_user.id,
    )).first()
    if res is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session.delete(res)
    session.commit()
    return