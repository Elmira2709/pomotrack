def test_duplicate_category_returns_409(client, user_a, create_category):
    create_category(user_a, "Work")
    r = client.post("/categories/", json={"name": "Work"}, headers=user_a)
    assert r.status_code == 409


def test_delete_category_with_tasks_returns_409(client, user_a, create_category, create_task):
    category = create_category(user_a, "Work")
    create_task(user_a, "task in category", category_id=category["id"])
    r = client.delete(f"/categories/{category['id']}", headers=user_a)
    assert r.status_code == 409