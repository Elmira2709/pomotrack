from fastapi import FastAPI
from pydantic import BaseModel, Field


class Task(BaseModel):
    id: int
    title: str
    done: bool
    category: int

app = FastAPI()


tasks = [
    Task(id=1, title="Do homework", done=True, category=1),
    Task(id=2, title="Do exersice", done=False, category=1),
    Task(id=3, title="Learn English", done=True, category=2)
]

@app.get("/tasks")
async def get_list(done: bool | None = None, category: int | None = None):
    result = []
    if done is None and category is None:
        return tasks
    
    for i in tasks:
        if i.done == done and i.category == category:
            result.append(i) 
        elif done is None and i.category == category or category is None and i.done == done: 
            result.append(i)
    return result        

@app.get("/tasks/{task_id}") 
async def get_task(task_id: int):
    for i in tasks:
        if i["id"] == task_id:
            return i
    return {'error': 'not found'}