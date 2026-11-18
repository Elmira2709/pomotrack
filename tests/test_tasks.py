def test_create_task_returns_201_and_fields(client, user_a):
    r = client.post("/tasks/", json={"title": "Read docs"}, headers=user_a)
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Read docs"
    assert body["id"] > 0


def test_filter_tasks_by_done(client, user_a, create_task):
    create_task(user_a, "open one", done=False)
    create_task(user_a, "finished one", done=True)
    r = client.get("/tasks/?done=true", headers=user_a)
    assert r.status_code == 200
    assert [t["title"] for t in r.json()] == ["finished one"]


def test_patch_changes_only_given_field(client, user_a, create_task):
    task = create_task(user_a, "Old title", done=False)
    r = client.patch(f"/tasks/{task['id']}", json={"done": True}, headers=user_a)
    assert r.status_code == 200
    assert r.json()["done"] is True
    assert r.json()["title"] == "Old title"


def test_create_task_with_missing_category_returns_404(client, user_a):
    r = client.post("/tasks/", json={"title": "x", "category_id": 999}, headers=user_a)
    assert r.status_code == 404


def test_create_task_with_empty_title_returns_422(client, user_a):
    r = client.post("/tasks/", json={"title": ""}, headers=user_a)
    assert r.status_code == 422