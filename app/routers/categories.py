from fastapi import APIRouter, status, Query, HTTPException, Path
from typing import Annotated
from sqlmodel import select
from ..models import CategoryPublic, Category, CategoryCreate, Task
from ..dependencies import CategoryDep
from ..database import SessionDep

router = APIRouter(prefix="/categories",
                   tags=["categories"])

@router.get("/", response_model=list[CategoryPublic])
def get_categories(session: SessionDep, skip: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 10): # синхронная
    categories = session.exec(select(Category).offset(skip).limit(limit)).all() # запрос к бд с лимитом, all нужен чтоб суметь превратить в список
    return categories

@router.post("/", response_model=CategoryPublic, status_code=201)
def create_categorie(category_create: CategoryCreate, session: SessionDep): # сессия сиинхронная (id пока не проверяю)
    res = session.exec(select(Category).where(Category.name == category_create.name)) #session.exec - "выполни этот запрос"
    if res.first(): # отдай 1 строку запроса
        raise HTTPException(status_code=409, detail='Category already in categories table')    
    db_category = Category.model_validate(category_create) # перекладывает уже проверенные данные из одной модели в другую
    session.add(db_category)  # запомни - надо бдет сохранить объект
    session.commit() # уже записывает
    session.refresh(db_category) # перечитывает
    return db_category

@router.get("/{category_id}/tasks", response_model=list[Task])
def get_task_by_category(categor_current: CategoryDep, session: SessionDep):
    res = session.exec(select(Task).where(Task.category_id == categor_current.id)).all()
    return res

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)   
def del_category(categor_current: CategoryDep, session: SessionDep): 
    q = session.exec(select(Task).where(Task.category_id == categor_current.id)).first()
    if q:
        raise HTTPException(status_code=409, detail="You have task by this category")
    session.delete(categor_current)
    session.commit()
    return
