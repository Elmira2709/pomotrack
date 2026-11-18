from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from sqlalchemy import func
from ..models import Category, Task, StatsAnswer, StatsCategory, PomodoroSession
from ..database import SessionDep
from ..dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/stats",
                   tags=["stats"],
                   dependencies=[Depends(get_current_user)])

@router.get("/summary", response_model=StatsAnswer)
def get_stats(session: SessionDep, current_user: CurrentUser,
              date_from: date | None = None, date_to: date | None = None):
    if date_to is None:
        date_to = datetime.now(timezone.utc).date()
    if date_from is None:
        date_from = date_to - timedelta(days=6)
    if date_from > date_to:
        raise HTTPException(status_code=422, detail='Time not correct')

    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)

    rows = session.exec(
        select(PomodoroSession.started_at, PomodoroSession.ended_at).where(
            PomodoroSession.user_id == current_user.id,
            PomodoroSession.type == "work",
            PomodoroSession.started_at >= start,
            PomodoroSession.ended_at <= end,
        )
    ).all()
    summ_min = sum((ended - started).total_seconds() for started, ended in rows) / 60
    num_done_tasks = session.exec(select(func.count(Task.id)).where(
        Task.user_id == current_user.id,
        Task.done == True,
    )).one()
    return StatsAnswer(num_work_session=len(rows),
                       summ_min=round(summ_min),
                       num_done_tasks=num_done_tasks)


@router.get("/by-category", response_model=list[StatsCategory])
def get_stats_by_category(session: SessionDep, current_user: CurrentUser):
    rows = session.exec(
        select(Category.name, PomodoroSession.started_at, PomodoroSession.ended_at)
        .join(Task, PomodoroSession.task_id == Task.id)
        .join(Category, Task.category_id == Category.id)
        .where(PomodoroSession.user_id == current_user.id,
               PomodoroSession.type == "work")
    ).all()
    totals: dict[str, float] = {}
    for name, started, ended in rows:
        totals[name] = totals.get(name, 0) + (ended - started).total_seconds() / 60
    return [StatsCategory(name=name, time=minutes) for name, minutes in totals.items()]