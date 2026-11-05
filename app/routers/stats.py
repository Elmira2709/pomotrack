from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from sqlalchemy import func
from ..models import  Category, Task, StatsAnswer, StatsCategory, PomodoroSession
from ..database import SessionDep


router = APIRouter(prefix="/stats",
                   tags=["stats"])

@router.get("/summary", response_model=StatsAnswer)
def get_stats(session: SessionDep, date_from: date | None = None, date_to: date | None = None):
    
    if date_to is None:
        date_to = datetime.now(timezone.utc).date()
    if date_from is None:   
        date_from = date_to - timedelta(days=6)
    if date_from > date_to:
        raise HTTPException(status_code=422, detail='Time not correct')    


    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)

    query = select(
        func.count(PomodoroSession.id),
        func.sum(PomodoroSession.time),).where(
            PomodoroSession.type == "work",
            PomodoroSession.started_at >= start,
            PomodoroSession.ended_at <= end,
        )
    num_work_session, summ_min = session.exec(query).one()
    num_done_tasks = session.exec(select(func.count(Task.id)).where(Task.done == True)).one()
    stats = StatsAnswer(num_work_session=num_work_session,
                        summ_min=summ_min or 0,
                        num_done_tasks=num_done_tasks)
    return stats

@router.get("/by-category", response_model=list[StatsCategory])
def get_stats_by_category(session: SessionDep):
    res = session.exec(select(func.sum(PomodoroSession.time), Category.name)
             .join(Task, PomodoroSession.task_id == Task.id)
             .join(Category, Task.category_id == Category.id)
             .where(PomodoroSession.type == "work")
             .group_by(Category.name)).all()
    return [StatsCategory(name=name, time=time) for time, name in res]