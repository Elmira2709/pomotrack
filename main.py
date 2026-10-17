from datetime import datetime
from typing import Annotated
from enum import Enum

from fastapi import FastAPI, Query, HTTPException, status, Path, Depends
from pydantic import BaseModel, Field, NaiveDatetime
from sqlmodel import Field, Session, SQLModel, create_engine, select

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)] # канал связи с базой

# БД---------------------

class CategoryBase(SQLModel):
    name: str = Field(index=True, unique=True, min_length=1, max_length=50)

class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True) # None означает ещё не присвоен

class CategoryPublic(CategoryBase):
    id: int

class CategoryCreate(CategoryBase):
    pass    
      
# БД---------------------

class TaskBase(SQLModel):
    title: str = Field(index=True, unique=True, min_length=1, max_length=100) # описывает атрибут класса-модели (наследника SQLModel).
    done: bool | None = None 
    category_id: int | None = Field(default=None, gt=0)

class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    category_id: int | None = Field(default=None, gt=0, foreign_key="category.id")
    created_at: NaiveDatetime = Field(default_factory=lambda: datetime.now()) # вызывает её при каждом создании задачи, 
    # и каждый раз получается новое время

class TaskCreate(TaskBase):
    pass

class TaskPublic(TaskBase):
    id: int

class TaskUpdate(TaskBase):
    title: str | None = Field(default=None, min_length=1, max_length=100) 

class OrderBy(str, Enum):
    id = "id"
    title = "title"    

class TaskFilters(BaseModel):
    done: bool | None = None
    category_id: int | None = Field(default=None, gt=0)
    search: str | None = Field(default=None, min_length=1, max_length=50)
    order_by: OrderBy = OrderBy.id  
    skip: Annotated[int, Query(ge=0)] = 0 
    limit: Annotated[int, Query(ge=1, le=100)] = 10  


app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()  


TaskID = Annotated[int, Path(gt=0)]
CategoryID = Annotated[int, Path(gt=0)]

def category_found(id: CategoryID, session: SessionDep):
    res = session.get(Category, id)
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
    q = session.exec(select(Task).where(Task.category_id == categor_current.id))
    if q:
        raise HTTPException(status_code=409, detail="You have task by this category")
    session.delete(categor_current)
    session.commit()
    return
