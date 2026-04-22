from __future__ import annotations

from typing import Any, TypeVar

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel

from cybersec_platform.contracts.api import (
    CellPatchIn,
    DeleteColumnsIn,
    DeleteRowsIn,
    EditorPageOut,
    EditorSaveOut,
    EditorSessionCreateIn,
    EditorSessionOut,
)
from cybersec_platform.db.session import get_settings

_ResponseModel = TypeVar("_ResponseModel", bound=BaseModel)


async def create_editor_session(file_path: str, payload: EditorSessionCreateIn) -> EditorSessionOut:
    return await _request_data_processing(
        "/editor-sessions",
        method="POST",
        payload={"file_path": file_path, **payload.model_dump(mode="json")},
        response_model=EditorSessionOut,
    )


async def get_editor_page(session_id: str, page: int, sheet_name: str | None = None) -> EditorPageOut:
    params: dict[str, Any] = {"page": page}
    if sheet_name:
        params["sheet_name"] = sheet_name
    return await _request_data_processing(
        f"/editor-sessions/{session_id}",
        method="GET",
        params=params,
        response_model=EditorPageOut,
    )


async def update_editor_cells(session_id: str, payload: CellPatchIn) -> EditorSessionOut:
    return await _request_data_processing(
        f"/editor-sessions/{session_id}/cells",
        method="PATCH",
        payload=payload.model_dump(mode="json"),
        response_model=EditorSessionOut,
    )


async def delete_editor_rows(session_id: str, payload: DeleteRowsIn) -> EditorSessionOut:
    return await _request_data_processing(
        f"/editor-sessions/{session_id}/rows/delete",
        method="POST",
        payload=payload.model_dump(mode="json"),
        response_model=EditorSessionOut,
    )


async def delete_editor_columns(session_id: str, payload: DeleteColumnsIn) -> EditorSessionOut:
    return await _request_data_processing(
        f"/editor-sessions/{session_id}/columns/delete",
        method="POST",
        payload=payload.model_dump(mode="json"),
        response_model=EditorSessionOut,
    )


async def save_editor_session(session_id: str) -> EditorSaveOut:
    return await _request_data_processing(
        f"/editor-sessions/{session_id}/save",
        method="POST",
        response_model=EditorSaveOut,
    )


async def discard_editor_session(session_id: str) -> None:
    await _request_data_processing(
        f"/editor-sessions/{session_id}",
        method="DELETE",
        response_model=None,
    )


async def _request_data_processing(
    path: str,
    method: str,
    response_model: type[_ResponseModel] | None,
    payload: Any | None = None,
    params: dict[str, Any] | None = None,
) -> _ResponseModel | None:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method,
                f"{settings.data_processing_service_url}{path}",
                json=payload,
                params=params,
            )
            response.raise_for_status()
            if response_model is None:
                return None
            return response_model.model_validate(response.json())
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data processing service is unavailable") from exc
    except httpx.HTTPStatusError as exc:
        detail = "Data processing service request failed"
        try:
            payload = exc.response.json()
            if isinstance(payload, dict):
                detail = str(payload.get("detail") or detail)
        except ValueError:
            detail = exc.response.text or detail
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
