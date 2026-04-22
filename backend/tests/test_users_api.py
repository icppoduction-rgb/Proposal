from __future__ import annotations


def _admin_headers(client):
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    assert login.status_code == 200
    tokens = login.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_user_crud_and_session_status(client):
    headers = _admin_headers(client)

    created = client.post(
        "/api/users",
        json={
            "email": "user-one@example.com",
            "password": "user-one-password",
            "role": "analyst",
            "full_name": "User One",
            "is_active": False,
        },
        headers=headers,
    )
    assert created.status_code == 201
    created_payload = created.json()
    assert created_payload["session_status"] == "inactive"
    assert created_payload["is_active"] is False

    listed = client.get("/api/users", headers=headers)
    assert listed.status_code == 200
    users = listed.json()
    created_user = next(item for item in users if item["id"] == created_payload["id"])
    assert created_user["full_name"] == "User One"
    assert created_user["role_name"] == "analyst"
    assert created_user["session_status"] == "inactive"

    updated = client.put(
        f"/api/users/{created_payload['id']}",
        json={
            "email": "user-one-updated@example.com",
            "password": "updated-user-secret",
            "role": "admin",
            "full_name": "User One Updated",
            "is_active": True,
        },
        headers=headers,
    )
    assert updated.status_code == 200
    updated_payload = updated.json()
    assert updated_payload["email"] == "user-one-updated@example.com"
    assert updated_payload["role_name"] == "admin"
    assert updated_payload["session_status"] == "active"
    assert updated_payload["is_active"] is True

    deleted = client.delete(f"/api/users/{created_payload['id']}", headers=headers)
    assert deleted.status_code == 200

    listed_after_delete = client.get("/api/users", headers=headers)
    assert listed_after_delete.status_code == 200
    assert all(item["id"] != created_payload["id"] for item in listed_after_delete.json())


def test_user_create_rejects_short_password(client):
    headers = _admin_headers(client)

    response = client.post(
        "/api/users",
        json={"email": "short-pass@example.com", "password": "short-password", "role": "analyst", "is_active": True},
        headers=headers,
    )

    assert response.status_code == 422


def test_user_update_rejects_duplicate_email(client):
    headers = _admin_headers(client)

    first = client.post(
        "/api/users",
        json={"email": "first@example.com", "password": "first-user-secret", "role": "analyst", "is_active": True},
        headers=headers,
    )
    second = client.post(
        "/api/users",
        json={"email": "second@example.com", "password": "second-user-secret", "role": "analyst", "is_active": True},
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.put(
        f"/api/users/{second.json()['id']}",
        json={"email": "first@example.com"},
        headers=headers,
    )

    assert response.status_code == 409
