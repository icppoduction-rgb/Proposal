"""EN: API routes for the structured log browsing section.
RU: API-маршруты для раздела просмотра структурированных логов.
"""

from __future__ import annotations

from datetime import date, time

from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import get_current_user
from backend.app.schemas.logs import LogQueryOut, LogQueryParams
from backend.app.services.logs import list_available_log_services, query_logs

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/services", response_model=list[str], dependencies=[Depends(get_current_user)])
async def get_log_services() -> list[str]:
    """EN: List services that currently expose structured JSONL logs.
    RU: Возвращает список сервисов, для которых доступны структурированные JSONL-логи.
    """

    return await list_available_log_services()


@router.get("", response_model=LogQueryOut, dependencies=[Depends(get_current_user)])
async def get_logs(
    service: list[str] | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    time_from: time | None = Query(default=None),
    time_to: time | None = Query(default=None),
    level: str | None = Query(default=None),
    function: str | None = Query(default=None),
    message: str | None = Query(default=None),
    error_text: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> LogQueryOut:
    """EN: Return filtered application logs for the Logs UI section.
    RU: Возвращает отфильтрованные логи приложения для UI-раздела Logs.
    """

    params = LogQueryParams(
        services=service or [],
        date_from=date_from,
        date_to=date_to,
        time_from=time_from,
        time_to=time_to,
        level=level,
        function=function,
        message=message,
        error_text=error_text,
        search=search,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )
    return await query_logs(params)
