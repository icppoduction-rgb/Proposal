from __future__ import annotations

import json
import logging
from pathlib import Path

from cybersec_platform.observability.logging import JsonFileHandler


def test_json_file_handler_writes_required_fields(tmp_path: Path):
    service_name = "unit-service"
    logger = logging.getLogger("unit-service-test")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(JsonFileHandler(service_name=service_name, logs_root=tmp_path))

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        logger.exception(
            "Test failure",
            extra={
                "function": "test_json_file_handler_writes_required_fields",
                "request": {"authorization": "secret", "path": "/demo"},
            },
        )

    log_file = next((tmp_path / service_name).glob(f"{service_name}-*.json.log"))
    payload = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert payload["timestamp"]
    assert payload["level"] == "ERROR"
    assert payload["function"] == "test_json_file_handler_writes_required_fields"
    assert payload["request"]["authorization"] == "***REDACTED***"
    assert payload["message"] == "Test failure"
    assert payload["error"]["type"] == "RuntimeError"
    assert "stack_trace" in payload["error"]


def test_json_file_handler_uses_context_when_request_missing(tmp_path: Path):
    service_name = "context-service"
    logger = logging.getLogger("context-service-test")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(JsonFileHandler(service_name=service_name, logs_root=tmp_path))

    from cybersec_platform.observability.logging import request_context

    with request_context({"authorization": "secret", "path": "/health"}):
        logger.info("Context propagated", extra={"function": "context_test"})

    log_file = next((tmp_path / service_name).glob(f"{service_name}-*.json.log"))
    payload = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert payload["request"]["authorization"] == "***REDACTED***"
    assert payload["request"]["path"] == "/health"
