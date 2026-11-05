from fastapi import FastAPI
from .routers import tasks
from .routers import categories, sessions, stats, auth, users

app = FastAPI()

app.include_router(categories.router)
app.include_router(sessions.router)
app.include_router(stats.router)
app.include_router(tasks.router)
app.include_router(auth.router)
app.include_router(users.router)