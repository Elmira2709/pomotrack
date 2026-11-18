from fastapi import APIRouter, Query, status, Depends
from typing import Annotated
from sqlmodel import select
from ..models import (TaskPublic, TaskFilters, Task, TaskCreate, TaskUpdate,
                      PomodoroSession, SesAnswer)
from ..dependencies import find_category, TaskDep, CurrentUser, get_current_user
from ..database import SessionDep

router = APIRouter(prefix="/tasks",
                   tags=["tasks"],
                   dependencies=[Depends(get_current_user)])

@router.get("/", response_model=list[TaskPublic])
def get_list(filters: Annotated[TaskFilters, Query()], session: SessionDep, current_user: CurrentUser):
    query = select(Task).where(Task.user_id == current_user.id)
    if filters.done is not None:
        query = query.where(filters.done == Task.done)
    if filters.category_id is not None:
        query = query.where(filters.category_id == Task.category_id)
    if filters.search is not None:
        query = query.where(Task.title.ilike(f"%{filters.search}%"))
    query = query.order_by(getattr(Task, filters.order_by.value.lower()))
    return session.exec(query.offset(filters.skip).limit(filters.limit)).all()

@router.post("/", response_model=TaskPublic, status_code=201)
def create_task(task: TaskCreate, session: SessionDep, current_user: CurrentUser):
    if task.category_id is not None:
        find_category(session, current_user, task.category_id)
    db_task = Task.model_validate(task, update={"user_id": current_user.id})
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.get("/{task_id}", response_model=TaskPublic)
def get_task(task: TaskDep):
    return task

@router.put("/{task_id}", response_model=TaskPublic)
def update_all_task(task_current: TaskDep, task: TaskCreate, session: SessionDep, current_user: CurrentUser):
    if task.category_id is not None:
        find_category(session, current_user, task.category_id)
    task_current.sqlmodel_update(task)
    session.add(task_current)
    session.commit()
    session.refresh(task_current)
    return task_current

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def del_task(task_current: TaskDep, session: SessionDep):
    session.delete(task_current)
    session.commit()
    return

@router.patch("/{task_id}", response_model=TaskPublic)
def update_task(task_current: TaskDep, task: TaskUpdate, session: SessionDep, current_user: CurrentUser):
    if task.category_id is not None:
        find_category(session, current_user, task.category_id)
    task_data = task.model_dump(exclude_unset=True)
    task_current.sqlmodel_update(task_data)
    session.add(task_current)
    session.commit()
    session.refresh(task_current)
    return task_current

@router.get("/{task_id}/sessions", response_model=list[SesAnswer])
def get_session_task(session: SessionDep, task_current: TaskDep, current_user: CurrentUser):
    return session.exec(select(PomodoroSession).where(
        PomodoroSession.task_id == task_current.id,
        PomodoroSession.user_id == current_user.id,
    )).all()