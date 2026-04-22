from __future__ import annotations

from datetime import timedelta

from backend.app.core.security import create_token


def test_login_and_me(client):
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"


def test_refresh_returns_new_token_pair(client):
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    assert login.status_code == 200
    tokens = login.json()

    refresh = client.post(f"/api/auth/refresh?refresh_token={tokens['refresh_token']}")
    assert refresh.status_code == 200
    refreshed_tokens = refresh.json()
    assert refreshed_tokens["access_token"]
    assert refreshed_tokens["refresh_token"]
    assert refreshed_tokens["refresh_token"] != tokens["refresh_token"]


def test_rbac_blocks_non_admin_creation(client):
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    tokens = login.json()
    create = client.post(
        "/api/users",
        json={"email": "analyst@example.com", "password": "analyst123456789", "role": "analyst", "is_active": True},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert create.status_code == 201

    analyst_login = client.post("/api/auth/login", json={"email": "analyst@example.com", "password": "analyst123456789"})
    analyst_tokens = analyst_login.json()
    denied = client.get("/api/users", headers={"Authorization": f"Bearer {analyst_tokens['access_token']}"})
    assert denied.status_code == 403


def test_inactive_user_cannot_log_in(client):
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    tokens = login.json()
    create = client.post(
        "/api/users",
        json={"email": "inactive@example.com", "password": "inactive12345678", "role": "analyst", "is_active": False},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert create.status_code == 201

    inactive_login = client.post("/api/auth/login", json={"email": "inactive@example.com", "password": "inactive12345678"})
    assert inactive_login.status_code == 401


def test_expired_access_token_returns_401(client):
    expired_token = create_token("expired-user", timedelta(minutes=-1), "access")

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


def test_expired_refresh_token_returns_401(client):
    expired_refresh_token = create_token("expired-user", timedelta(minutes=-1), "refresh")

    response = client.post(f"/api/auth/refresh?refresh_token={expired_refresh_token}")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token expired"
