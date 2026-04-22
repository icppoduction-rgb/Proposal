from __future__ import annotations

from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_platform.contracts.api import ArtifactStatus, InferenceRequest
from cybersec_platform.db import ModelArtifact, get_async_session
from cybersec_platform.ml.inference import InferenceEngine, load_model_bundle
from cybersec_platform.observability import configure_logging, log_event, request_context

app = FastAPI(title="Model Analiz Service", version="0.1.0")
logger = configure_logging("model-analiz")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """EN: Persist structured access logs for model inference HTTP requests.
    RU: Сохраняет структурированные access-логи для HTTP-запросов сервиса инференса.
    """

    started_at = perf_counter()
    with request_context(
        {
            "type": "http",
            "service": "model-analiz",
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
                "Model service request failed",
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
            "Model service request completed",
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
async def ready(session: AsyncSession = Depends(get_async_session)) -> dict[str, str]:
    """EN: Readiness probe that checks database access.
    RU: Readiness-probe, проверяющая доступность базы данных.
    """

    await session.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.post("/predict")
async def predict(payload: InferenceRequest, session: AsyncSession = Depends(get_async_session)) -> dict[str, list[dict]]:
    """EN: Run prediction against a promoted artifact and return record-level scores.
    RU: Выполняет предсказание по опубликованному артефакту и возвращает оценки по записям.
    """

    artifact = await session.get(ModelArtifact, payload.model_artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Model artifact not found")
    if artifact.status != ArtifactStatus.PROMOTED.value:
        raise HTTPException(status_code=400, detail="Artifact is not promoted")
    bundle = load_model_bundle(artifact.artifact_path)
    predictions = InferenceEngine().predict(payload, bundle)
    log_event(
        logger,
        20,
        "Inference predictions generated",
        function="predict",
        model_artifact_id=payload.model_artifact_id,
        record_count=len(payload.records),
        prediction_count=len(predictions),
    )
    return {"predictions": predictions}
