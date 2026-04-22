"""EN: Backend gateway client for the dedicated internal log-service.
RU: Backend gateway-клиент для выделенного внутреннего log-service.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException, status

from backend.app.schemas.logs import LogQueryOut, LogQueryParams
from cybersec_platform.db.session import get_settings
from cybersec_platform.observability import log_event

logger = logging.getLogger(__name__)


def _sanitize_query_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """EN: Remove blank query parameters before calling log-service.
    RU: Удаляет пустые query-параметры перед вызовом log-service.

    Args:
        params: EN: Raw query parameter mapping. RU: Исходное отображение query-параметров.

    Returns:
        EN: Sanitized mapping or None when there is nothing to send.
        RU: Очищенное отображение или None, если отправлять нечего.

    Side Effects:
        EN: Does not mutate the incoming mapping.
        RU: Не изменяет входное отображение.

    Raises:
        EN: Does not raise.
        RU: Исключения не выбрасывает.
    """

    if not params:
        return None

    sanitized: dict[str, Any] = {}
    for key, value in params.items():
        if value is None or value == "":
            continue
        if isinstance(value, list):
            filtered = [item for item in value if item not in (None, "")]
            if filtered:
                sanitized[key] = filtered
            continue
        sanitized[key] = value
    return sanitized or None

async def list_available_log_services() -> list[str]:
    """EN: Fetch the current list of log-producing services from log-service.
    RU: Получает актуальный список сервисов-источников логов из log-service.

    Args:
        None.

    Returns:
        EN: List of service names available for browsing.
        RU: Список имён сервисов, доступных для просмотра.

    Side Effects:
        EN: Performs an HTTP request to the internal log-service.
        RU: Выполняет HTTP-запрос к внутреннему log-service.

    Raises:
        EN: HTTPException with 503 status when log-service cannot be reached.
        RU: HTTPException со статусом 503, если log-service недоступен.
    """

    payload = await _request_log_service("/services", params=None)
    if not isinstance(payload, list):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid log-service response")
    log_event(logger, logging.INFO, "Fetched log service catalog", function="list_available_log_services", service_count=len(payload))
    return [str(item) for item in payload]


async def query_logs(params: LogQueryParams) -> LogQueryOut:
    """EN: Fetch one cursor page of log entries from the internal log-service.
    RU: Получает одну cursor-страницу лог-записей из внутреннего log-service.

    Args:
        params: EN: Filter and cursor parameters for the downstream log query. RU: Параметры фильтрации и курсора для downstream-запроса логов.

    Returns:
        EN: Cursor-based log page validated against the public API schema.
        RU: Cursor-based страница логов, провалидированная по публичной API-схеме.

    Side Effects:
        EN: Performs an HTTP request to the internal log-service.
        RU: Выполняет HTTP-запрос к внутреннему log-service.

    Raises:
        EN: HTTPException with 503/502 status when downstream service is unavailable or invalid.
        RU: HTTPException со статусом 503/502, если downstream-сервис недоступен или вернул некорректный ответ.
    """

    query_params: dict[str, Any] = {
        "service": params.services,
        "date_from": params.date_from.isoformat() if params.date_from else None,
        "date_to": params.date_to.isoformat() if params.date_to else None,
        "time_from": params.time_from.isoformat() if params.time_from else None,
        "time_to": params.time_to.isoformat() if params.time_to else None,
        "level": params.level,
        "function": params.function,
        "message": params.message,
        "error_text": params.error_text,
        "search": params.search,
        "sort": params.sort,
        "cursor": params.cursor,
        "limit": params.limit,
    }
    payload = await _request_log_service("/entries", params=query_params)
    try:
        result = LogQueryOut.model_validate(payload)
    except Exception as exc:  # pragma: no cover - exercised via API contract tests.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid log-service response") from exc
    log_event(
        logger,
        logging.INFO,
        "Fetched log cursor page",
        function="query_logs",
        item_count=len(result.items),
        has_more=result.has_more,
        services=params.services,
        sort=params.sort,
    )
    return result


async def _request_log_service(path: str, params: dict[str, Any] | None) -> Any:
    """EN: Perform a typed HTTP request to the internal log-service.
    RU: Выполняет типизированный HTTP-запрос к внутреннему log-service.

    Args:
        path: EN: Relative path on the downstream service. RU: Относительный путь на downstream-сервисе.
        params: EN: Query-string payload forwarded to the service. RU: Query-string payload, проксируемый в сервис.

    Returns:
        EN: JSON-decoded response body.
        RU: JSON-декодированное тело ответа.

    Side Effects:
        EN: Opens an outbound HTTP connection.
        RU: Открывает исходящее HTTP-соединение.

    Raises:
        EN: HTTPException when the downstream call fails.
        RU: HTTPException, если downstream-вызов завершился ошибкой.
    """

    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{settings.log_service_url}{path}", params=_sanitize_query_params(params))
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Log service is unavailable") from exc
    except httpx.HTTPStatusError as exc:
        detail = "Log service request failed"
        try:
            payload = exc.response.json()
            if isinstance(payload, dict):
                detail = str(payload.get("detail") or detail)
        except ValueError:
            detail = exc.response.text or detail
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
