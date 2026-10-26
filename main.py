from datetime import timezone, timedelta
from typing import Annotated
from fastapi import FastAPI, Query, HTTPException, status, Path, Depends
from sqlmodel import Session, SQLModel, create_engine, select
from config import func
from models import Category, CategoryPublic, CategoryCreate, TaskCreate, Task, TaskPublic, TaskUpdate, TaskFilters 
from models import PomodoroSession, SesAnswer, SesCreate, SesFilters

engine = create_engine(func().database_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)] # канал связи с базой

# БД---------------------

app = FastAPI()


TaskID = Annotated[int, Path(gt=0)]
CategoryID = Annotated[int, Path(gt=0)]

def category_found(category_id: CategoryID, session: SessionDep):
    res = session.get(Category, category_id)
    if res:
        return res
    raise HTTPException(status_code=404, detail="Category not found") 
        
CategoryDep = Annotated[Category, Depends(category_found)] # зависимость

def task_found(task_id: TaskID, session: SessionDep):
    res = session.get(Task, task_id)
    if res:
        return res
    raise HTTPException(status_code=404, detail="Task not found")

TaskDep = Annotated[Task, Depends(task_found)]



#------------------------------------------------------
@app.get("/tasks", response_model=list[TaskPublic])
def get_list(filters: Annotated[TaskFilters, Query()], session: SessionDep):
    query = select(Task)
    if filters.done is not None:
        query = query.where(filters.done == Task.done)   
    if filters.category_id is not None:
        query = query.where(filters.category_id == Task.category_id)
    if filters.search is not None:
        query = query.where(Task.title.ilike(f"%{filters.search}%"))
    query = query.order_by(getattr(Task, filters.order_by.value.lower()))           
    result = session.exec(query.offset(filters.skip).limit(filters.limit)).all() 
    return result                        
 
@app.post("/tasks", response_model=TaskPublic, status_code=201)
def create_task(task: TaskCreate, session: SessionDep):
    category_found(task.category_id, session)
    db_task = Task.model_validate(task)   
    session.add(db_task)  # запомни - надо бдет сохранить объект
    session.commit() # уже записывает
    session.refresh(db_task) # перечитывает
    return db_task 


@app.get("/tasks/{task_id}", response_model=TaskPublic) 
def get_task(task: TaskDep):
    return task

@app.put("/tasks/{task_id}", response_model=TaskPublic)
def update_all_task(task_current: TaskDep, task: TaskCreate, session: SessionDep):
    if task.category_id is not None:
        category_found(task.category_id, session)   
    task_current.sqlmodel_update(task)
    session.add(task_current)
    session.commit() # уже записывает
    session.refresh(task_current) # перечитывает
    return task_current  

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def del_task(task_current: TaskDep, session: SessionDep):
    session.delete(task_current)
    session.commit()
    return   

@app.patch("/tasks/{task_id}", response_model=TaskPublic)
def update_task(task_current: TaskDep, task: TaskUpdate, session: SessionDep):
    if task.category_id is not None:
        category_found(task.category_id, session)
    task_data = task.model_dump(exclude_unset=True)    
    task_current.sqlmodel_update(task_data)
    session.add(task_current)
    session.commit()
    session.refresh(task_current)
    return task_current
      

# Категории----------------------------------------------

@app.get("/categories", response_model=list[CategoryPublic])
def get_categories(session: SessionDep, skip: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 10): # синхронная
    categories = session.exec(select(Category).offset(skip).limit(limit)).all() # запрос к бд с лимитом, all нужен чтоб суметь превратить в список
    return categories

@app.post("/categories", response_model=CategoryPublic, status_code=201)
def create_categorie(category_create: CategoryCreate, session: SessionDep): # сессия сиинхронная (id пока не проверяю)
    res = session.exec(select(Category).where(Category.name == category_create.name)) #session.exec - "выполни этот запрос"
    if res.first(): # отдай 1 строку запроса
        raise HTTPException(status_code=409, detail='Category already in categories table')    
    db_category = Category.model_validate(category_create) # перекладывает уже проверенные данные из одной модели в другую
    session.add(db_category)  # запомни - надо бдет сохранить объект
    session.commit() # уже записывает
    session.refresh(db_category) # перечитывает
    return db_category

@app.get("/categories/{category_id}/tasks", response_model=list[Task])
def get_task_by_category(categor_current: CategoryDep, session: SessionDep):
    res = session.exec(select(Task).where(Task.category_id == categor_current.id)).all()
    return res

@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)   
def del_category(categor_current: CategoryDep, session: SessionDep): 
    q = session.exec(select(Task).where(Task.category_id == categor_current.id)).first()
    if q:
        raise HTTPException(status_code=409, detail="You have task by this category")
    session.delete(categor_current)
    session.commit()
    return

# Сессии---------------------------------------
@app.post("/sessions", response_model=SesAnswer, status_code=201)
def create_ses(session: SessionDep, ses: SesCreate):
    db_ses = PomodoroSession.model_validate(ses) # создаёт объект модели из данных, попутно проверяя их
    session.add(db_ses)
    session.commit()
    session.refresh(db_ses)
    return db_ses

@app.get("/sessions", response_model=list[SesAnswer])
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

@app.get("/tasks/{task_id}/sessions", response_model=SesAnswer)
def get_session_task(session: SessionDep, task_id: TaskDep):
    result = session.exec(select(PomodoroSession).where(PomodoroSession.task_id == task_id)).all()
    return result

@app.delete("/sessions/{session_id}", status_code=204)
def delete_session(session: SessionDep, session_id: Annotated[int, Path(gt=0)]):
    res = session.get(PomodoroSession, session_id)
    if res:
        session.delete(res)
        session.commit()
        return
    raise HTTPException(status_code=404, detail="Session not found")
    

    

