from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import (
    routes_auth,
    routes_auto_training,
    routes_datasets,
    routes_explanations,
    routes_feature_schemas,
    routes_health,
    routes_i18n,
    routes_inference,
    routes_logs,
    routes_models,
    routes_tasks,
    routes_training,
    routes_users,
)
from backend.app.db.init_db import init_db, seed_defaults
from backend.app.services.outbox import publish_pending_outbox_messages, run_outbox_publisher
from cybersec_platform.db import get_async_session
from cybersec_platform.db.session import get_settings
from cybersec_platform.observability import configure_logging, log_event, request_context


logger = configure_logging("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """EN: Initialize persistent backend state and default records on startup.
    RU: Инициализирует постоянное состояние backend и записи по умолчанию при запуске.
    """

    log_event(logger, 20, "Backend startup initiated", function="lifespan", request={"type": "service", "service": "backend"})
    await init_db()
    async for session in get_async_session():
        await seed_defaults(session)
        break
    stop_event = asyncio.Event()
    publisher_task = asyncio.create_task(run_outbox_publisher(stop_event), name="backend-outbox-publisher")
    await publish_pending_outbox_messages()
    log_event(logger, 20, "Backend startup completed", function="lifespan", request={"type": "service", "service": "backend"})
    try:
        yield
    finally:
        stop_event.set()
        publisher_task.cancel()
        try:
            await publisher_task
        except asyncio.CancelledError:
            pass
        log_event(logger, 20, "Backend shutdown completed", function="lifespan", request={"type": "service", "service": "backend"})


settings = get_settings()

app = FastAPI(title="Cybersecurity Detection Platform API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in settings.backend_cors_origins.split(",") if item.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """EN: Bind request metadata and persist structured access logs for every HTTP call.
    RU: Привязывает метаданные запроса и сохраняет структурированные access-логи для каждого HTTP-вызова.
    """

    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    request_payload = {
        "type": "http",
        "method": request.method,
        "path": request.url.path,
        "query": str(request.url.query),
        "client": request.client.host if request.client else None,
        "correlation_id": correlation_id,
    }
    started_at = perf_counter()
    with request_context(request_payload):
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(
                "HTTP request failed",
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
            "HTTP request completed",
            function="log_requests",
            status_code=response.status_code,
            duration_ms=round((perf_counter() - started_at) * 1000, 2),
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response

for router in (
    routes_auth.router,
    routes_users.router,
    routes_auto_training.router,
    routes_datasets.router,
    routes_feature_schemas.router,
    routes_training.router,
    routes_models.router,
    routes_inference.router,
    routes_explanations.router,
    routes_logs.router,
    routes_tasks.router,
    routes_health.router,
    routes_i18n.router,
):
    app.include_router(router, prefix="/api")
