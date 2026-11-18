def test_register_returns_201_without_password(client):
    r = client.post("/auth/register", json={"username": "alice", "password": "password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "alice"
    assert "password" not in body and "hash_password" not in body


def test_register_duplicate_username_returns_409(client):
    data = {"username": "alice", "password": "password123"}
    client.post("/auth/register", json=data)
    r = client.post("/auth/register", json=data)
    assert r.status_code == 409


def test_login_with_wrong_password_returns_401(client):
    client.post("/auth/register", json={"username": "alice", "password": "password123"})
    r = client.post("/auth/token", data={"username": "alice", "password": "wrongpass1"})
    assert r.status_code == 401


def test_users_me_without_token_returns_401(client):
    assert client.get("/users/me").status_code == 401


def test_tasks_without_token_returns_401(client):
    assert client.get("/tasks/").status_code == 401


def test_users_me_with_token_returns_current_user(client, user_a):
    r = client.get("/users/me", headers=user_a)
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_settings_created_with_defaults_on_register(client, user_a):
    r = client.get("/users/me/settings", headers=user_a)
    assert r.status_code == 200
    assert r.json()["work_minutes"] == 25