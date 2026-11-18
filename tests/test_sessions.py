def test_session_ended_before_started_returns_422(client, user_a, create_task, ses_payload):
    task = create_task(user_a)
    payload = ses_payload(task["id"])
    payload["started_at"], payload["ended_at"] = payload["ended_at"], payload["started_at"]
    r = client.post("/sessions/", json=payload, headers=user_a)
    assert r.status_code == 422


def test_work_session_without_task_id_returns_422(client, user_a, ses_payload):
    r = client.post("/sessions/", json=ses_payload(None, type="work"), headers=user_a)
    assert r.status_code == 422


def test_valid_work_session_returns_201(client, user_a, create_task, ses_payload):
    task = create_task(user_a)
    r = client.post("/sessions/", json=ses_payload(task["id"]), headers=user_a)
    assert r.status_code == 201
    assert r.json()["time"] == 25