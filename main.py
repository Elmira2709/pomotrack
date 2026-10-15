from typing import Annotated
from enum import Enum

from fastapi import FastAPI, Query, HTTPException, status, Path, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, SQLModel, create_engine, select

# БД---------------------
class TableCategory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

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

class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=100) # описывает атрибут класса-модели (наследника BaseModel).
    done: bool
    category: int = Field(gt=0) 

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int

class OrderBy(str, Enum):
    id = "id"
    title = "title"    

class TaskFilters(BaseModel):
    done: bool | None = None
    category: int | None = Field(default=None, gt=0)
    search: str | None = Field(default=None, min_length=1, max_length=50)
    order_by: OrderBy = OrderBy.id    

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    done: bool | None = None
    category: int | None = Field(default=None, gt=0)


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int  


app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()  


tasks = [
    Task(id=1, title="Do homework", done=True, category=1),
    Task(id=2, title="Do exersice", done=False, category=1),
    Task(id=3, title="Learn English", done=True, category=2)
]

TaskID = Annotated[int, Path(gt=0)]
CategoryID = Annotated[int, Path(gt=0)]

def category_found(category_id: CategoryID, session: SessionDep):
    res = session.get(TableCategory, category_id)
    if res:
        return res
    raise HTTPException(status_code=404, detail="Category not found") 
        

Category_for_loop = Annotated[TableCategory, Depends(category_found)] # зависимость

def for_loop(task_id: TaskID):
    for i in tasks:
        if i.id == task_id:
            return i
    raise HTTPException(status_code=404, detail="Task not found")

Task_for_loop = Annotated[Task, Depends(for_loop)]

class CommonParameters:
    def __init__(self, skip: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 10):
        self.skip = skip   
        self.limit = limit

Commons = Annotated[CommonParameters, Depends()] # работает только когда слева стоит класс, если слева функция то пишем тип

@app.get("/tasks", response_model=list[Task])
async def get_list(commons: Commons, filters: Annotated[TaskFilters, Query()]):
    result = tasks.copy()
    if filters.done is not None:
        new = []
        for i in result:
            if i.done == filters.done:
                new.append(i)
        result = new
    if filters.category is not None:
        new = []
        for j in result:
            if j.category == filters.category:
                new.append(j)
        result = new
    if filters.search is not None:
        new = []
        for k in result:
            if filters.search.lower() in k.title.lower():
                new.append(k)
        result = new
    result.sort(key=lambda x: getattr(x, filters.order_by.value.lower()))            
    return result[commons.skip:commons.skip + commons.limit]                        
 
@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate, session: SessionDep):
    category_found(task.category, session)
    task_id = max((i.id for i in tasks), default=0) + 1    
    new = Task(id=task_id, title=task.title, done=task.done, category=task.category)
    tasks.append(new)
    return new 


@app.get("/tasks/{task_id}", response_model=Task) 
async def get_task(task_new: Task_for_loop):
    return task_new

@app.put("/tasks/{task_id}", response_model=Task)
def update_all_task(task_current: Task_for_loop, task: TaskCreate, session: SessionDep):
    category_found(task.category, session)
    num = tasks.index(task_current)
    tasks[num] = Task(id=task_current.id, title=task.title, done=task.done, category=task.category)
    return tasks[num]  

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def del_task(task_current: Task_for_loop):
    tasks.remove(task_current)
    return   

@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_current: Task_for_loop, task: TaskUpdate, session: SessionDep):
    if task.category is not None:
        category_found(task.category, session)
    update_data = task.model_dump(exclude_unset=True) # превращает в словарь только то, что прислал клиент
    num = tasks.index(task_current)
    update_t = task_current.model_copy(update=update_data)
    tasks[num] = update_t  
    return update_t      

# Категории----------------------------------------------

@app.get("/categories", response_model=list[Category])
def get_categories(commons: Commons, session: SessionDep): # синхронная
    categories = session.exec(select(TableCategory).offset(commons.skip).limit(commons.limit)).all() # запрос к бд с лимитом, all нужен чтоб суметь превратить в список
    return categories

@app.post("/categories", response_model=Category, status_code=201) # ПОТЕРЯ ВАЛИДАЦИИ
def create_categorie(table_category: TableCategory, session: SessionDep): # сессия сиинхронная (id пока не проверяю)
    res = session.exec(select(TableCategory).where(TableCategory.name == table_category.name)) #session.exec - "выполни этот запрос"
    if res.first(): # отдай 1 строку запроса
        raise HTTPException(status_code=409, detail='Category already in categories table')    
    session.add(table_category)  # запомни - надо бдет сохранить объект
    session.commit() # уже записывает
    session.refresh(table_category) # перечитывает
    return table_category

@app.get("/categories/{category_id}/tasks", response_model=list[Task])
def get_task_by_category(categor_current: Category_for_loop):
    res = []
    for i in tasks:
        if i.category == categor_current.id:
            res.append(i)
    return res

@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)   
def del_category(categor_current: Category_for_loop, session: SessionDep): 
    for i in tasks:
        if i.category == categor_current.id:
            raise HTTPException(status_code=409, detail="You have task by this category")
    session.delete(categor_current)
    session.commit()
    return
