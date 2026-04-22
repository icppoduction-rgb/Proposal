from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_health_endpoint():
    from services.model_analiz.app.main import app

    client = TestClient(app)
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
