from __future__ import annotations

from backend.app.main import app
from cybersec_platform.db import get_async_session

def test_ready_returns_service_unavailable_when_database_probe_fails(client):
    class BrokenSession:
        async def execute(self, *_args, **_kwargs):
            raise RuntimeError("database unavailable")

    async def override_session():
        yield BrokenSession()

    app.dependency_overrides[get_async_session] = override_session
    try:
        response = client.get("/api/health/ready")
    finally:
        app.dependency_overrides.pop(get_async_session, None)

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is not ready"
