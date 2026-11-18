def test_user_b_does_not_see_task_of_a_in_list(client, user_a, user_b, create_task):
    create_task(user_a, "secret task")
    r = client.get("/tasks/", headers=user_b)
    assert r.status_code == 200
    assert r.json() == []


def test_user_b_cannot_get_patch_or_delete_task_of_a(client, user_a, user_b, create_task):
    task = create_task(user_a, "secret task")
    url = f"/tasks/{task['id']}"
    assert client.get(url, headers=user_b).status_code == 404
    assert client.patch(url, json={"title": "hacked"}, headers=user_b).status_code == 404
    assert client.delete(url, headers=user_b).status_code == 404
    r = client.get(url, headers=user_a)
    assert r.status_code == 200
    assert r.json()["title"] == "secret task"


def test_user_b_can_create_category_with_same_name(client, user_a, user_b, create_category):
    create_category(user_a, "Work")
    r = client.post("/categories/", json={"name": "Work"}, headers=user_b)
    assert r.status_code == 201


def test_user_b_cannot_attach_task_to_category_of_a(client, user_a, user_b, create_category):
    category = create_category(user_a, "Work")
    r = client.post("/tasks/", json={"title": "x", "category_id": category["id"]}, headers=user_b)
    assert r.status_code == 404


def test_user_b_cannot_create_session_for_task_of_a(client, user_a, user_b, create_task, ses_payload):
    task = create_task(user_a)
    r = client.post("/sessions/", json=ses_payload(task["id"]), headers=user_b)
    assert r.status_code == 404


def test_user_b_stats_are_zero_when_a_has_data(client, user_a, user_b, create_task, ses_payload):
    task = create_task(user_a, done=True)
    client.post("/sessions/", json=ses_payload(task["id"]), headers=user_a)
    r = client.get("/stats/summary", headers=user_b)
    assert r.json() == {"num_work_session": 0, "summ_min": 0, "num_done_tasks": 0}