from __future__ import annotations

from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from cybersec_platform.contracts.api import (
    CellPatchIn,
    DeleteColumnsIn,
    DeleteRowsIn,
    EditorPageOut,
    EditorSaveOut,
    EditorSessionOut,
)
from cybersec_platform.db.session import get_settings
from cybersec_platform.observability import configure_logging, log_event, request_context
from services.data_processing.app.service import (
    DataProcessingError,
    create_editor_session,
    delete_editor_columns,
    delete_editor_rows,
    delete_editor_session,
    get_editor_page,
    get_raw_root,
    update_editor_cells,
    save_editor_session,
)

app = FastAPI(title="Data Processing Service", version="0.1.0")
logger = configure_logging("data-processing-service")


class EditorSessionOpenIn(BaseModel):
    file_path: str
    page_size: int = Field(default=50, ge=1, le=200)
    sheet_name: str | None = None


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = perf_counter()
    with request_context(
        {
            "type": "http",
            "service": "data-processing-service",
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
                "Data processing request failed",
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
            "Data processing request completed",
            function="log_requests",
            status_code=response.status_code,
            duration_ms=round((perf_counter() - started_at) * 1000, 2),
        )
        return response


@app.exception_handler(DataProcessingError)
async def handle_data_processing_error(_: Request, exc: DataProcessingError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    Path(get_settings().tmp_path).mkdir(parents=True, exist_ok=True)
    get_raw_root()
    return {"status": "ready"}


@app.post("/editor-sessions", response_model=EditorSessionOut, status_code=201)
async def open_editor_session(payload: EditorSessionOpenIn) -> EditorSessionOut:
    return create_editor_session(payload.file_path, page_size=payload.page_size, sheet_name=payload.sheet_name)


@app.get("/editor-sessions/{session_id}", response_model=EditorPageOut)
async def get_editor_session_page(
    session_id: str,
    page: int = Query(default=1, ge=1),
    sheet_name: str | None = Query(default=None),
) -> EditorPageOut:
    return get_editor_page(session_id, page=page, sheet_name=sheet_name)


@app.patch("/editor-sessions/{session_id}/cells", response_model=EditorSessionOut)
async def patch_editor_session_cells(session_id: str, payload: CellPatchIn) -> EditorSessionOut:
    return update_editor_cells(session_id, [item.model_dump(mode="json") for item in payload.patches])


@app.post("/editor-sessions/{session_id}/rows/delete", response_model=EditorSessionOut)
async def remove_editor_session_rows(session_id: str, payload: DeleteRowsIn) -> EditorSessionOut:
    return delete_editor_rows(session_id, payload.row_indices)


@app.post("/editor-sessions/{session_id}/columns/delete", response_model=EditorSessionOut)
async def remove_editor_session_columns(session_id: str, payload: DeleteColumnsIn) -> EditorSessionOut:
    return delete_editor_columns(session_id, payload.columns)


@app.post("/editor-sessions/{session_id}/save", response_model=EditorSaveOut)
async def persist_editor_session(session_id: str) -> EditorSaveOut:
    return save_editor_session(session_id)


@app.delete("/editor-sessions/{session_id}", status_code=204)
async def discard_session(session_id: str) -> None:
    delete_editor_session(session_id)
