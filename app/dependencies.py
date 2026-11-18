from typing import Annotated
from fastapi import HTTPException, Path, Depends, status
from sqlmodel import select, Session
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from .models import Category, Task, User
from .database import SessionDep
from .config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except (InvalidTokenError, ValueError):
        raise credentials_exception
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

TaskID = Annotated[int, Path(gt=0)]
CategoryID = Annotated[int, Path(gt=0)]

def find_category(session: Session, user: User, category_id: int) -> Category:
    res = session.exec(
        select(Category).where(Category.id == category_id, Category.user_id == user.id)
    ).first()
    if res is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return res

def find_task(session: Session, user: User, task_id: int) -> Task:
    res = session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == user.id)
    ).first()
    if res is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return res

def category_found(category_id: CategoryID, session: SessionDep, current_user: CurrentUser):
    return find_category(session, current_user, category_id)

CategoryDep = Annotated[Category, Depends(category_found)]

def task_found(task_id: TaskID, session: SessionDep, current_user: CurrentUser):
    return find_task(session, current_user, task_id)

TaskDep = Annotated[Task, Depends(task_found)]