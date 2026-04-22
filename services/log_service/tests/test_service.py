from __future__ import annotations

import json
from pathlib import Path

from cybersec_platform.observability import LogQueryParams
from services.log_service.app.main import _normalize_optional_query_value
from services.log_service.app.service import list_available_log_services, query_logs


def _write_log_fixture(root: Path) -> None:
    backend_dir = root / "backend"
    training_dir = root / "training-service"
    backend_dir.mkdir(parents=True, exist_ok=True)
    training_dir.mkdir(parents=True, exist_ok=True)

    (backend_dir / "backend-2026-04-21.json.log").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-04-21T10:00:00+00:00",
                        "level": "INFO",
                        "service": "backend",
                        "function": "seed_defaults",
                        "request": {"type": "service"},
                        "message": "Startup completed",
                        "error": None,
                        "context": {"duration_ms": 1.5},
                    }
                ),
                "not-json",
                json.dumps(
                    {
                        "timestamp": "2026-04-21T11:00:00+00:00",
                        "level": "ERROR",
                        "service": "backend",
                        "function": "validate_dataset",
                        "request": {"type": "http", "authorization": "secret"},
                        "message": "Dataset validation failed",
                        "error": {"type": "ValueError", "message": "broken"},
                        "context": {},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (training_dir / "training-service-2026-04-22.json.log").write_text(
        json.dumps(
            {
                "timestamp": "2026-04-22T09:00:00+00:00",
                "level": "WARNING",
                "service": "training-service",
                "function": "run_training",
                "request": {"type": "task", "token": "hide-me"},
                "message": "Training skipped",
                "error": None,
                "context": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_query_logs_lists_services_and_sanitizes_payload(tmp_path: Path):
    logs_root = tmp_path / "logs"
    _write_log_fixture(logs_root)

    assert list_available_log_services(logs_root) == ["backend", "training-service"]

    payload = query_logs(LogQueryParams(services=["backend"], sort="desc", limit=10), logs_root=logs_root)
    assert payload.available_services == ["backend", "training-service"]
    assert payload.items[0].level == "ERROR"
    assert payload.items[0].request["authorization"] == "***REDACTED***"
    assert any(not item.is_valid_json for item in payload.items)


def test_query_logs_supports_cursor_and_search(tmp_path: Path):
    logs_root = tmp_path / "logs"
    _write_log_fixture(logs_root)

    first_page = query_logs(
        LogQueryParams(services=["backend"], sort="asc", limit=1),
        logs_root=logs_root,
    )
    assert len(first_page.items) == 1
    assert first_page.has_more is True
    assert first_page.next_cursor

    second_page = query_logs(
        LogQueryParams(services=["backend"], sort="asc", limit=1, cursor=first_page.next_cursor),
        logs_root=logs_root,
    )
    assert len(second_page.items) == 1
    assert second_page.items[0].id != first_page.items[0].id


def test_normalize_optional_query_value_collapses_blanks():
    assert _normalize_optional_query_value(None) is None
    assert _normalize_optional_query_value("") is None
    assert _normalize_optional_query_value("   ") is None
    assert _normalize_optional_query_value("backend") == "backend"
