from __future__ import annotations

from backend.app.schemas.logs import LogQueryOut


def _login(client):
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    return response.json()["access_token"]


def test_logs_api_proxies_services_endpoint(client, monkeypatch):
    token = _login(client)

    async def fake_list_available_log_services():
        return ["backend", "training-service"]

    monkeypatch.setattr("backend.app.api.routes_logs.list_available_log_services", fake_list_available_log_services)

    response = client.get("/api/logs/services", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == ["backend", "training-service"]


def test_logs_api_proxies_cursor_response(client, monkeypatch):
    token = _login(client)

    async def fake_query_logs(params):
        assert params.services == ["backend"]
        assert params.limit == 25
        assert params.cursor == "cursor-1"
        return LogQueryOut(
            items=[
                {
                    "id": "backend:backend-2026-04-21.json.log:1",
                    "timestamp": "2026-04-21T10:00:00+00:00",
                    "service": "backend",
                    "level": "ERROR",
                    "function": "validate_dataset",
                    "message": "Dataset validation failed",
                    "request": {"path": "/api/datasets/1/validate"},
                    "error": {"type": "ValueError", "message": "broken"},
                    "context": {},
                    "source_file": "/tmp/backend-2026-04-21.json.log",
                    "line_number": 1,
                    "is_valid_json": True,
                    "raw_line": None,
                }
            ],
            next_cursor="cursor-2",
            has_more=True,
            invalid_rows_in_page=0,
            available_services=["backend"],
        )

    monkeypatch.setattr("backend.app.api.routes_logs.query_logs", fake_query_logs)

    response = client.get(
        "/api/logs?service=backend&search=validation&cursor=cursor-1&limit=25",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["has_more"] is True
    assert payload["next_cursor"] == "cursor-2"
    assert payload["items"][0]["level"] == "ERROR"
