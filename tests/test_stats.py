def test_summary_sums_minutes_on_known_data(client, user_a, create_task, ses_payload):
    task = create_task(user_a, done=True)
    client.post("/sessions/", json=ses_payload(task["id"], minutes=25, minutes_ago=100), headers=user_a)
    client.post("/sessions/", json=ses_payload(task["id"], minutes=30, minutes_ago=30), headers=user_a)
    r = client.get("/stats/summary", headers=user_a)
    assert r.status_code == 200
    assert r.json() == {"num_work_session": 2, "summ_min": 55, "num_done_tasks": 1}


def test_summary_for_empty_period_returns_zeros(client, user_a):
    r = client.get("/stats/summary", headers=user_a)
    assert r.status_code == 200
    assert r.json() == {"num_work_session": 0, "summ_min": 0, "num_done_tasks": 0}