from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./backend_test.db"
os.environ["SYNC_DATABASE_URL"] = "sqlite:///./backend_test.db"
os.environ["RAW_DATA_PATH"] = str(Path.cwd() / "test-data" / "raw")
os.environ["ARCHIVE_DATA_PATH"] = str(Path.cwd() / "test-data" / "archives")
os.environ["NORMALIZED_DATA_PATH"] = str(Path.cwd() / "test-data" / "normalized")
os.environ["MODELS_PATH"] = str(Path.cwd() / "test-data" / "models")
os.environ["REPORTS_PATH"] = str(Path.cwd() / "test-data" / "reports")
os.environ["EXPLANATIONS_PATH"] = str(Path.cwd() / "test-data" / "explanations")
os.environ["LOGS_PATH"] = str(Path.cwd() / "test-data" / "logs")
os.environ["LOG_SERVICE_URL"] = "http://log-service:8002"
os.environ["TMP_PATH"] = str(Path.cwd() / "test-data" / "tmp")

from backend.app.main import app  # noqa: E402
from cybersec_platform.db import Base, get_sync_engine  # noqa: E402
from cybersec_platform.db.session import async_session_factory  # noqa: E402


@pytest.fixture(autouse=True)
def mock_celery(monkeypatch):
    class Result:
        id = "test-task-id"

    monkeypatch.setattr("backend.app.services.tasks.celery_app.send_task", lambda *args, **kwargs: Result())


@pytest.fixture(autouse=True)
def clean_test_data():
    root = Path.cwd() / "test-data"
    for child in root.iterdir() if root.exists() else []:
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("raw", "archives", "normalized", "models", "reports", "explanations", "logs", "tmp"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    engine = get_sync_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    asyncio.run(async_session_factory.kw["bind"].dispose())
    yield


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
