from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app import models  


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, username: str) -> dict:
    password = "password123"
    r = client.post("/auth/register", json={"username": username, "password": password})
    assert r.status_code == 201
    r = client.post("/auth/token", data={"username": username, "password": password})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def user_a(client: TestClient) -> dict:
    return _register_and_login(client, "alice")


@pytest.fixture
def user_b(client: TestClient) -> dict:
    return _register_and_login(client, "bobby")


@pytest.fixture
def create_task(client: TestClient):
    def _create(headers: dict, title: str = "Task", **extra) -> dict:
        r = client.post("/tasks/", json={"title": title, **extra}, headers=headers)
        assert r.status_code == 201
        return r.json()
    return _create


@pytest.fixture
def create_category(client: TestClient):
    def _create(headers: dict, name: str = "Work") -> dict:
        r = client.post("/categories/", json={"name": name}, headers=headers)
        assert r.status_code == 201
        return r.json()
    return _create


@pytest.fixture
def ses_payload():
    def _payload(task_id: int | None, minutes: int = 25, minutes_ago: int = 10,
                 type: str = "work") -> dict:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        ended = now - timedelta(minutes=minutes_ago)
        started = ended - timedelta(minutes=minutes)
        return {
            "type": type,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "task_id": task_id,
        }
    return _payload