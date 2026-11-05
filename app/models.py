from pydantic import BaseModel, NaiveDatetime, computed_field, model_validator, AwareDatetime
from sqlmodel import SQLModel, Field
from typing import Annotated
from enum import Enum
from fastapi import Query
from datetime import datetime, timezone, date

class CategoryBase(SQLModel):
    name: str = Field(index=True, unique=True, min_length=1, max_length=50)

class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True) # None означает ещё не присвоен

class CategoryPublic(CategoryBase):
    id: int

class CategoryCreate(CategoryBase):
    pass    
      


class TaskBase(SQLModel):
    title: str = Field(index=True, unique=True, min_length=1, max_length=100) # описывает атрибут класса-модели (наследника SQLModel).
    done: bool | None = None 
    category_id: int | None = Field(default=None, gt=0)

class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    category_id: int | None = Field(default=None, gt=0, foreign_key="category.id")
    created_at: NaiveDatetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # вызывает её при каждом создании задачи, 
    # и каждый раз получается новое время
    description: str | None = Field(default=None, max_length=500)

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

class TypeSession(str, Enum):
    work = 'work'
    short_break = "short_break" 
    long_break = "long_break"

class PomodoroSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    type: TypeSession
    started_at: AwareDatetime
    ended_at: AwareDatetime
    task_id: int | None = Field(default=None, gt=0, foreign_key="task.id")

    @computed_field
    @property
    def time(self) -> float:
        return (self.ended_at - self.started_at).total_seconds() / 60  

class SesCreate(BaseModel):
    type: TypeSession
    started_at: AwareDatetime
    ended_at: AwareDatetime
    task_id: int | None = None
    
    @model_validator(mode='after')
    def check(self):
        if self.started_at >= self.ended_at or self.started_at > datetime.now(timezone.utc) or self.ended_at > datetime.now(timezone.utc) :
            raise ValueError('Time is not correct')
        if self.type == 'work' and self.task_id is None:
            raise ValueError('No task_id')
        if self.type != 'work' and self.task_id is not None:
            raise ValueError("Break doesn't have task_id") 
        if (self.ended_at - self.started_at).total_seconds() / 60 < 1 or (self.ended_at - self.started_at).total_seconds() / 60 > 120:
            raise ValueError('Time is not correct')
        return self

class SesAnswer(BaseModel):
    id: int
    type: TypeSession
    started_at: datetime
    ended_at: datetime
    time: float
    task_id: int | None
    
class SesFilters(BaseModel):
    type: TypeSession | None = None
    task_id: int | None = None
    date_from: date | None = None 
    date_to: date | None = None
    skip: Annotated[int, Query(ge=0)] = 0 
    limit: Annotated[int, Query(ge=1, le=100)] = 10

class StatsAnswer(BaseModel):
    num_work_session: int 
    summ_min: int
    num_done_tasks: int

class StatsCategory(BaseModel):
    name: str
    time: float

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)    
    hash_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserIn(BaseModel):
    username: str = Field(min_length=2)
    password: str = Field(min_length=8)

class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool

class Token(SQLModel):
    access_token: str
    token_type: str

