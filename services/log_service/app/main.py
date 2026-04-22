"""EN: FastAPI entrypoint for the dedicated structured log-service.
RU: FastAPI entrypoint для выделенного сервиса структурированных логов.
"""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import TypeVar

from fastapi import FastAPI, Query, Request

from cybersec_platform.db.session import get_settings
from cybersec_platform.observability import LogQueryOut, LogQueryParams, configure_logging, log_event, request_context
from services.log_service.app.service import list_available_log_services, query_logs

app = FastAPI(title="Log Service", version="0.1.0")
logger = configure_logging("log-service")
_QueryValue = TypeVar("_QueryValue", bound=str)


def _normalize_optional_query_value(value: _QueryValue | None) -> _QueryValue | None:
    """EN: Collapse blank query-string values into None before validation.
    RU: Схлопывает пустые значения query-string в None до валидации.

    Args:
        value: EN: Raw optional query-string value. RU: Сырое опциональное значение query-string.

    Returns:
        EN: Trimmed string or None for blank values.
        RU: Обрезанная строка или None для пустых значений.

    Side Effects:
        EN: Does not mutate external state.
        RU: Не изменяет внешнее состояние.

    Raises:
        EN: Does not raise.
        RU: Исключения не выбрасывает.
    """

    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """EN: Persist structured access logs for every log-service HTTP request.
    RU: Сохраняет структурированные access-логи для каждого HTTP-запроса log-service.
    """

    started_at = perf_counter()
    with request_context(
        {
            "type": "http",
            "service": "log-service",
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "client": request.client.host if request.client else None,
        }
    ):
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(
                "Log-service request failed",
                extra={
                    "function": "log_requests",
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                },
            )
            raise
        log_event(
            logger,
            20,
            "Log-service request completed",
            function="log_requests",
            status_code=response.status_code,
            duration_ms=round((perf_counter() - started_at) * 1000, 2),
        )
        return response


@app.get("/health/live")
async def live() -> dict[str, str]:
    """EN: Lightweight liveness probe without external dependencies.
    RU: Лёгкая liveness-probe без внешних зависимостей.
    """

    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    """EN: Readiness probe that verifies the logs root can be resolved.
    RU: Readiness-probe, проверяющая доступность корневой директории логов.
    """

    logs_root = Path(get_settings().logs_path)
    logs_root.mkdir(parents=True, exist_ok=True)
    return {"status": "ready"}


@app.get("/services", response_model=list[str])
async def get_services() -> list[str]:
    """EN: Return service names that currently expose structured JSONL logs.
    RU: Возвращает имена сервисов, для которых сейчас доступны структурированные JSONL-логи.
    """

    return list_available_log_services()


@app.get("/entries", response_model=LogQueryOut)
async def get_entries(
    service: list[str] | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    time_from: str | None = Query(default=None),
    time_to: str | None = Query(default=None),
    level: str | None = Query(default=None),
    function: str | None = Query(default=None),
    message: str | None = Query(default=None),
    error_text: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> LogQueryOut:
    """EN: Return one cursor page of filtered structured log entries.
    RU: Возвращает одну cursor-страницу отфильтрованных структурированных лог-записей.
    """

    params = LogQueryParams(
        services=service or [],
        date_from=_normalize_optional_query_value(date_from),
        date_to=_normalize_optional_query_value(date_to),
        time_from=_normalize_optional_query_value(time_from),
        time_to=_normalize_optional_query_value(time_to),
        level=_normalize_optional_query_value(level),
        function=_normalize_optional_query_value(function),
        message=_normalize_optional_query_value(message),
        error_text=_normalize_optional_query_value(error_text),
        search=_normalize_optional_query_value(search),
        sort=sort,
        cursor=_normalize_optional_query_value(cursor),
        limit=limit,
    )
    return query_logs(params)
