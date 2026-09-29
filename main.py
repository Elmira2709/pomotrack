from fastapi import FastAPI
from pydantic import BaseModel
from Tasks import Tasks as tasks

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    done: bool
    category: int


@app.get("/tasks")
async def get_list(done: bool = None):
    result = []
    if done == None:
        return tasks
    for i in tasks:
        if i["done"] == done:
            result.append(i) 
    return result        

@app.get("/tasks/{task_id}") 
async def get_task(task_id: int):
    for i in tasks:
        if i["id"] == task_id:
            return i
    return {'error': 'not found'}