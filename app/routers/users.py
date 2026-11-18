from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from ..models import UserOut, UserSettings, SettingsPublic, SettingsUpdate
from ..dependencies import CurrentUser, get_current_user
from ..database import SessionDep

router = APIRouter(prefix="/users",
                   tags=["users"],
                   dependencies=[Depends(get_current_user)])

def _own_settings(session, user) -> UserSettings:
    res = session.exec(select(UserSettings).where(UserSettings.user_id == user.id)).first()
    if res is None:
        raise HTTPException(status_code=404, detail="Settings not found")
    return res

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: CurrentUser):
    return current_user

@router.get("/me/settings", response_model=SettingsPublic)
def read_my_settings(session: SessionDep, current_user: CurrentUser):
    return _own_settings(session, current_user)

@router.patch("/me/settings", response_model=SettingsPublic)
def update_my_settings(data: SettingsUpdate, session: SessionDep, current_user: CurrentUser):
    settings = _own_settings(session, current_user)
    settings.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True))
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings