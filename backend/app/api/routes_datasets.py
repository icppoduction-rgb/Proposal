from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import (
    DatasetOut,
    ManagedDatasetCreateIn,
    ManagedDatasetOut,
    MessageResponse,
    RawDatasetInspectIn,
    RawDatasetInspectOut,
    TaskRecordOut,
    UploadChunkOut,
    UploadCompleteOut,
    UploadSessionCreateIn,
    UploadSessionOut,
)
from backend.app.services.data_processing import (
    create_editor_session,
    delete_editor_columns,
    delete_editor_rows,
    discard_editor_session,
    get_editor_page,
    save_editor_session,
    update_editor_cells,
)
from backend.app.services.dataset_uploads import (
    DatasetUploadError,
    complete_upload_session,
    create_upload_session,
    discard_upload_session,
    get_session_file,
    get_session_payload_path,
    inspect_raw_file,
    normalize_relative_path,
    update_uploaded_chunk,
)
from backend.app.services.managed_datasets import (
    delete_all_managed_datasets,
    delete_managed_dataset,
    ensure_legacy_dataset_for_managed_dataset,
    ensure_registered_raw_file_is_available,
    get_managed_dataset,
    get_managed_dataset_by_name,
    list_managed_datasets,
)
from backend.app.services.raw_files import (
    delete_all_raw_files,
    delete_raw_file_record,
    ensure_raw_file_paths_available,
    get_raw_file,
    get_raw_file_by_relative_path,
    invalidate_datasets_for_raw_change,
    list_raw_file_models,
    register_uploaded_raw_files,
    relative_path_from_absolute,
    serialize_raw_file,
    sync_raw_file_records,
)
from backend.app.services.tasks import dispatch_task
from cybersec_platform.contracts.api import (
    CellPatchIn,
    DatasetManifest,
    DeleteColumnsIn,
    DeleteRowsIn,
    EditorPageOut,
    EditorSaveOut,
    EditorSessionCreateIn,
    EditorSessionOut,
    RawFileOut,
)
from cybersec_platform.db import Dataset, ManagedDataset, RawFile
from cybersec_platform.db.session import get_settings

router = APIRouter(prefix="/datasets", tags=["datasets"])


async def _require_raw_file(session: SessionDep, raw_file_id: str):
    raw_file = await get_raw_file(session, raw_file_id)
    if raw_file is None:
        raise HTTPException(status_code=404, detail="Raw file not found")
    return raw_file


def _ensure_editor_belongs_to_raw_file(expected_path: str, actual_path: str) -> None:
    if Path(actual_path).resolve() != Path(expected_path).resolve():
        raise HTTPException(status_code=404, detail="Editor session not found for this raw file")


async def _get_legacy_dataset_by_name(session: SessionDep, name: str) -> Dataset | None:
    result = await session.execute(select(Dataset).where(func.lower(Dataset.name) == name.strip().lower()))
    return result.scalars().first()


async def _get_legacy_dataset_by_storage_path(session: SessionDep, storage_path: str) -> Dataset | None:
    result = await session.execute(select(Dataset).where(Dataset.storage_path == storage_path))
    return result.scalars().first()


async def _ensure_legacy_dataset_registration_allowed(session: SessionDep, name: str, storage_path: str) -> None:
    duplicate_name = await _get_legacy_dataset_by_name(session, name)
    if duplicate_name is not None:
        raise HTTPException(status_code=409, detail="Dataset with this name already exists")

    duplicate_path = await _get_legacy_dataset_by_storage_path(session, storage_path)
    if duplicate_path is not None:
        raise HTTPException(status_code=409, detail="Dataset for this raw file already exists")


async def _upsert_legacy_raw_file_record(session: SessionDep, target: Path) -> RawFile:
    resolved_target = str(target.resolve())
    existing_raw_file = await session.execute(select(RawFile).where(RawFile.path == resolved_target))
    raw_file = existing_raw_file.scalar_one_or_none()
    if raw_file is None:
        raw_file = RawFile(name=target.name, path=resolved_target, size=target.stat().st_size)
        session.add(raw_file)
        await session.flush()
        return raw_file

    raw_file.name = target.name
    raw_file.size = target.stat().st_size
    await session.flush()
    return raw_file


@router.get("", response_model=list[DatasetOut], dependencies=[Depends(get_current_user)])
async def list_datasets(session: SessionDep) -> list[DatasetOut]:
    result = await session.execute(select(Dataset))
    return [DatasetOut.model_validate(item) for item in result.scalars().all()]


@router.get("/management", response_model=list[ManagedDatasetOut], dependencies=[Depends(get_current_user)])
async def list_dataset_management_records(session: SessionDep) -> list[ManagedDatasetOut]:
    return [ManagedDatasetOut.model_validate(item) for item in await list_managed_datasets(session)]


@router.post("/management", response_model=ManagedDatasetOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def register_dataset_management_record(payload: ManagedDatasetCreateIn, session: SessionDep) -> ManagedDatasetOut:
    duplicate = await get_managed_dataset_by_name(session, payload.name)
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Dataset with this name already exists")

    raw_file = await _require_raw_file(session, payload.raw_file_id)
    try:
        file_path = ensure_registered_raw_file_is_available(raw_file)
    except DatasetUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    item = ManagedDataset(
        raw_file_id=raw_file.id,
        name=payload.name,
        file_path=file_path,
        feature_set=sorted(payload.feature_set),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return ManagedDatasetOut.model_validate(item)


@router.delete("/management/{dataset_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def delete_dataset_management_record(dataset_id: str, session: SessionDep) -> MessageResponse:
    item = await get_managed_dataset(session, dataset_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Managed dataset not found")
    dataset_name = item.name
    await delete_managed_dataset(session, item)
    await session.commit()
    return MessageResponse(message=f"Managed dataset deleted: {dataset_name}")


@router.delete("/management", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def clear_dataset_management_records(session: SessionDep) -> MessageResponse:
    deleted_count = await delete_all_managed_datasets(session)
    await session.commit()
    return MessageResponse(message=f"Deleted managed datasets: {deleted_count}")


@router.post("/management/{dataset_id}/validate", response_model=TaskRecordOut, dependencies=[Depends(get_current_user)])
async def validate_managed_dataset(dataset_id: str, session: SessionDep) -> TaskRecordOut:
    managed_dataset = await get_managed_dataset(session, dataset_id)
    if managed_dataset is None:
        raise HTTPException(status_code=404, detail="Managed dataset not found")

    try:
        linked_dataset = await ensure_legacy_dataset_for_managed_dataset(session, managed_dataset)
        await session.commit()
    except DatasetUploadError as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    record = await dispatch_task(
        session,
        task_name="normalization.validate_dataset",
        object_type="dataset",
        object_id=linked_dataset.id,
        queue="normalization",
        kwargs={"dataset_id": linked_dataset.id},
    )
    return TaskRecordOut.model_validate(record)


@router.get("/raw-files", response_model=list[RawFileOut], dependencies=[Depends(get_current_user)])
async def list_raw_dataset_files(session: SessionDep) -> list[RawFileOut]:
    raw_files = await sync_raw_file_records(session)
    await session.commit()
    return [serialize_raw_file(item) for item in raw_files]


@router.delete("/raw-files/{raw_file_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def delete_raw_dataset_file(raw_file_id: str, session: SessionDep) -> MessageResponse:
    raw_file = await _require_raw_file(session, raw_file_id)
    try:
        await delete_raw_file_record(session, raw_file)
        await session.commit()
    except DatasetUploadError as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return MessageResponse(message=f"Raw file deleted: {raw_file.name}")


@router.delete("/raw-files", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def delete_all_raw_dataset_files(session: SessionDep) -> MessageResponse:
    try:
        deleted_count = await delete_all_raw_files(session)
        await session.commit()
    except DatasetUploadError as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return MessageResponse(message=f"Deleted raw files: {deleted_count}")


@router.post("/raw-files/inspect", response_model=RawDatasetInspectOut, dependencies=[Depends(get_current_user)])
async def inspect_dataset_file(payload: RawDatasetInspectIn, session: SessionDep) -> RawDatasetInspectOut:
    try:
        if payload.raw_file_id:
            raw_file = await _require_raw_file(session, payload.raw_file_id)
            relative_path = relative_path_from_absolute(raw_file.path)
        elif payload.relative_path:
            raw_file = await get_raw_file_by_relative_path(session, payload.relative_path)
            if raw_file is None:
                await sync_raw_file_records(session)
                await session.commit()
                raw_file = await get_raw_file_by_relative_path(session, payload.relative_path)
            if raw_file is None:
                raise HTTPException(status_code=404, detail="Raw file not found")
            relative_path = relative_path_from_absolute(raw_file.path)
        else:  # pragma: no cover - guarded by pydantic validator.
            raise HTTPException(status_code=400, detail="Raw file reference is required")
        return RawDatasetInspectOut.model_validate(inspect_raw_file(relative_path))
    except DatasetUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/raw-files/{raw_file_id}/editor-sessions", response_model=EditorSessionOut, dependencies=[Depends(get_current_user)])
async def open_raw_file_editor_session(
    raw_file_id: str,
    session: SessionDep,
    payload: EditorSessionCreateIn = Body(default_factory=EditorSessionCreateIn),
) -> EditorSessionOut:
    raw_file = await _require_raw_file(session, raw_file_id)
    editor_session = await create_editor_session(raw_file.path, payload)
    _ensure_editor_belongs_to_raw_file(raw_file.path, editor_session.file_path)
    return editor_session


@router.get("/raw-files/{raw_file_id}/editor-sessions/{session_id}", response_model=EditorPageOut, dependencies=[Depends(get_current_user)])
async def get_raw_file_editor_page(
    raw_file_id: str,
    session_id: str,
    session: SessionDep,
    page: int = Query(default=1, ge=1),
    sheet_name: str | None = Query(default=None),
) -> EditorPageOut:
    raw_file = await _require_raw_file(session, raw_file_id)
    editor_page = await get_editor_page(session_id, page=page, sheet_name=sheet_name)
    _ensure_editor_belongs_to_raw_file(raw_file.path, editor_page.file_path)
    return editor_page


@router.patch("/raw-files/{raw_file_id}/editor-sessions/{session_id}/cells", response_model=EditorSessionOut, dependencies=[Depends(get_current_user)])
async def patch_raw_file_editor_cells(
    raw_file_id: str,
    session_id: str,
    payload: CellPatchIn,
    session: SessionDep,
) -> EditorSessionOut:
    raw_file = await _require_raw_file(session, raw_file_id)
    editor_session = await update_editor_cells(session_id, payload)
    _ensure_editor_belongs_to_raw_file(raw_file.path, editor_session.file_path)
    return editor_session


@router.post("/raw-files/{raw_file_id}/editor-sessions/{session_id}/rows/delete", response_model=EditorSessionOut, dependencies=[Depends(get_current_user)])
async def delete_raw_file_editor_rows(
    raw_file_id: str,
    session_id: str,
    payload: DeleteRowsIn,
    session: SessionDep,
) -> EditorSessionOut:
    raw_file = await _require_raw_file(session, raw_file_id)
    editor_session = await delete_editor_rows(session_id, payload)
    _ensure_editor_belongs_to_raw_file(raw_file.path, editor_session.file_path)
    return editor_session


@router.post("/raw-files/{raw_file_id}/editor-sessions/{session_id}/columns/delete", response_model=EditorSessionOut, dependencies=[Depends(get_current_user)])
async def delete_raw_file_editor_columns_route(
    raw_file_id: str,
    session_id: str,
    payload: DeleteColumnsIn,
    session: SessionDep,
) -> EditorSessionOut:
    raw_file = await _require_raw_file(session, raw_file_id)
    editor_session = await delete_editor_columns(session_id, payload)
    _ensure_editor_belongs_to_raw_file(raw_file.path, editor_session.file_path)
    return editor_session


@router.post("/raw-files/{raw_file_id}/editor-sessions/{session_id}/save", response_model=EditorSaveOut, dependencies=[Depends(get_current_user)])
async def save_raw_file_editor_changes(raw_file_id: str, session_id: str, session: SessionDep) -> EditorSaveOut:
    raw_file = await _require_raw_file(session, raw_file_id)
    preview = await get_editor_page(session_id, page=1)
    _ensure_editor_belongs_to_raw_file(raw_file.path, preview.file_path)
    saved = await save_editor_session(session_id)
    raw_file.size = saved.size_bytes
    await invalidate_datasets_for_raw_change(session, raw_file.path)
    await session.commit()
    return saved


@router.delete("/raw-files/{raw_file_id}/editor-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
async def close_raw_file_editor_session(raw_file_id: str, session_id: str, session: SessionDep) -> None:
    raw_file = await _require_raw_file(session, raw_file_id)
    preview = await get_editor_page(session_id, page=1)
    _ensure_editor_belongs_to_raw_file(raw_file.path, preview.file_path)
    await discard_editor_session(session_id)


@router.post("/uploads/sessions", response_model=UploadSessionOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def init_dataset_upload_session(payload: UploadSessionCreateIn, session: SessionDep) -> UploadSessionOut:
    try:
        await ensure_raw_file_paths_available(session, [item.relative_path for item in payload.files])
        session_payload = create_upload_session([item.model_dump() for item in payload.files])
    except DatasetUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return UploadSessionOut.model_validate(session_payload)


@router.put("/uploads/sessions/{session_id}/files/{file_id}", response_model=UploadChunkOut, dependencies=[Depends(get_current_user)])
async def upload_dataset_chunk(session_id: str, file_id: str, request: Request) -> UploadChunkOut:
    try:
        session_payload = get_session_file(session_id, file_id)
        file_payload = next(item for item in session_payload["files"] if item["file_id"] == file_id)
        offset = int(request.headers.get("X-Chunk-Offset", "-1"))
        chunk_length = int(request.headers.get("X-Chunk-Length", "-1"))
        if offset < 0 or chunk_length <= 0:
            raise DatasetUploadError("Chunk offset and length are required")

        temp_path = get_session_payload_path(session_id, file_payload["relative_path"])
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        current_size = temp_path.stat().st_size if temp_path.exists() else 0
        if current_size != file_payload["uploaded_bytes"] or offset != current_size:
            raise DatasetUploadError(
                f"Chunk offset mismatch for {file_payload['relative_path']}: expected {file_payload['uploaded_bytes']}",
                status_code=409,
            )

        written = 0
        with temp_path.open("ab" if temp_path.exists() else "wb") as output:
            async for chunk in request.stream():
                if not chunk:
                    continue
                output.write(chunk)
                written += len(chunk)

        if written != chunk_length or offset + written > file_payload["size_bytes"]:
            with temp_path.open("r+b") as output:
                output.truncate(offset)
            raise DatasetUploadError(f"Invalid chunk length for {file_payload['relative_path']}")

        updated = update_uploaded_chunk(session_id, file_id, offset + written)
        updated_file = next(item for item in updated["files"] if item["file_id"] == file_id)
        return UploadChunkOut.model_validate(
            {
                "session_id": session_id,
                "file_id": file_id,
                "status": updated_file["status"],
                "uploaded_bytes": updated_file["uploaded_bytes"],
                "size_bytes": updated_file["size_bytes"],
            }
        )
    except DatasetUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/uploads/sessions/{session_id}/complete", response_model=UploadCompleteOut, dependencies=[Depends(get_current_user)])
async def finalize_dataset_upload_session(session_id: str, session: SessionDep) -> UploadCompleteOut:
    try:
        payload = complete_upload_session(session_id)
        uploaded_records = await register_uploaded_raw_files(session, payload["uploaded_files"])
        await session.commit()
        raw_files = [serialize_raw_file(item) for item in await list_raw_file_models(session)]
        return UploadCompleteOut(
            session_id=payload["session_id"],
            status=payload["status"],
            uploaded_files=[serialize_raw_file(item) for item in uploaded_records],
            raw_files=raw_files,
        )
    except DatasetUploadError as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.delete("/uploads/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
async def discard_dataset_upload_session(session_id: str) -> None:
    try:
        discard_upload_session(session_id)
    except DatasetUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def upload_dataset(
    session: SessionDep,
    manifest_json: str = Form(...),
    file: UploadFile = File(...),
) -> DatasetOut:
    manifest = DatasetManifest.model_validate_json(manifest_json)
    settings = get_settings()
    try:
        file_name = normalize_relative_path(Path(file.filename or "dataset.csv").name)
    except DatasetUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    raw_root = Path(settings.raw_data_path).resolve()
    target = (raw_root / file_name).resolve()
    if not target.is_relative_to(raw_root):
        raise HTTPException(status_code=400, detail="Raw file path is outside of the raw data root")
    if target.exists():
        raise HTTPException(status_code=409, detail=f"Raw dataset file already exists: {file_name}")

    await _ensure_legacy_dataset_registration_allowed(session, manifest.name, str(target))

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        await _upsert_legacy_raw_file_record(session, target)
        item = Dataset(
            name=manifest.name,
            source_type=manifest.source_type.value,
            description=manifest.description,
            manifest=manifest.model_dump(mode="json"),
            storage_path=str(target),
            lineage=manifest.lineage,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return DatasetOut.model_validate(item)
    except Exception:
        await session.rollback()
        target.unlink(missing_ok=True)
        raise


@router.post("/register", response_model=DatasetOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def register_dataset(payload: DatasetManifest, session: SessionDep) -> DatasetOut:
    settings = get_settings()
    try:
        raw_root = Path(settings.raw_data_path).resolve()
        target = (raw_root / normalize_relative_path(payload.file_name)).resolve()
    except DatasetUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not target.is_relative_to(raw_root):
        raise HTTPException(status_code=400, detail="Raw file path is outside of the raw data root")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=409, detail="Selected raw file does not exist")

    storage_path = str(target)
    await _ensure_legacy_dataset_registration_allowed(session, payload.name, storage_path)
    try:
        await _upsert_legacy_raw_file_record(session, target)
        item = Dataset(
            name=payload.name,
            source_type=payload.source_type.value,
            description=payload.description,
            manifest=payload.model_dump(mode="json"),
            storage_path=storage_path,
            lineage=payload.lineage,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return DatasetOut.model_validate(item)
    except Exception:
        await session.rollback()
        raise


@router.get("/{dataset_id}", response_model=DatasetOut, dependencies=[Depends(get_current_user)])
async def get_dataset(dataset_id: str, session: SessionDep) -> DatasetOut:
    item = await session.get(Dataset, dataset_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetOut.model_validate(item)


@router.post("/{dataset_id}/validate", response_model=TaskRecordOut, dependencies=[Depends(get_current_user)])
async def validate_dataset(dataset_id: str, session: SessionDep) -> TaskRecordOut:
    item = await session.get(Dataset, dataset_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    record = await dispatch_task(
        session,
        task_name="normalization.validate_dataset",
        object_type="dataset",
        object_id=item.id,
        queue="normalization",
        kwargs={"dataset_id": item.id},
    )
    return TaskRecordOut.model_validate(record)


@router.post("/{dataset_id}/trigger-parse", response_model=TaskRecordOut, dependencies=[Depends(get_current_user)])
async def trigger_parse(dataset_id: str, session: SessionDep) -> TaskRecordOut:
    item = await session.get(Dataset, dataset_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    record = await dispatch_task(
        session,
        task_name="normalization.validate_dataset",
        object_type="dataset",
        object_id=item.id,
        queue="normalization",
        kwargs={"dataset_id": item.id},
    )
    return TaskRecordOut.model_validate(record)
