from fastapi import APIRouter, Depends
from typing import Annotated
from ..models import User, UserOut
from ..dependencies import get_current_user

router = APIRouter(prefix="/users",
                   tags=["users"])

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
              
