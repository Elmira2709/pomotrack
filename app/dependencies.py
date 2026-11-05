from typing import Annotated
from fastapi import HTTPException, Path, Depends, status
from sqlmodel import select
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from .models import Category, Task
from .database import SessionDep
from .config import get_settings
from .models import User


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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except (InvalidTokenError, ValueError):
        raise credentials_exception
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise credentials_exception
    if session.exec(select(User).where(User.is_active == True)).first() is None:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user