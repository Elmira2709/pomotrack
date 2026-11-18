from fastapi import APIRouter, status, Query, HTTPException, Depends
from typing import Annotated
from sqlmodel import select
from ..models import CategoryPublic, Category, CategoryCreate, Task, TaskPublic
from ..dependencies import CategoryDep, CurrentUser, get_current_user
from ..database import SessionDep

router = APIRouter(prefix="/categories",
                   tags=["categories"],
                   dependencies=[Depends(get_current_user)])

@router.get("/", response_model=list[CategoryPublic])
def get_categories(session: SessionDep, current_user: CurrentUser,
                   skip: Annotated[int, Query(ge=0)] = 0,
                   limit: Annotated[int, Query(ge=1, le=100)] = 10):
    return session.exec(
        select(Category).where(Category.user_id == current_user.id).offset(skip).limit(limit)
    ).all()

@router.post("/", response_model=CategoryPublic, status_code=201)
def create_categorie(category_create: CategoryCreate, session: SessionDep, current_user: CurrentUser):
    res = session.exec(select(Category).where(
        Category.name == category_create.name,
        Category.user_id == current_user.id,
    ))
    if res.first():
        raise HTTPException(status_code=409, detail='Category already in categories table')
    db_category = Category.model_validate(category_create, update={"user_id": current_user.id})
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

@router.get("/{category_id}/tasks", response_model=list[TaskPublic])
def get_task_by_category(categor_current: CategoryDep, session: SessionDep, current_user: CurrentUser):
    return session.exec(select(Task).where(
        Task.category_id == categor_current.id,
        Task.user_id == current_user.id,
    )).all()

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def del_category(categor_current: CategoryDep, session: SessionDep):
    q = session.exec(select(Task).where(Task.category_id == categor_current.id)).first()
    if q:
        raise HTTPException(status_code=409, detail="You have task by this category")
    session.delete(categor_current)
    session.commit()
    return