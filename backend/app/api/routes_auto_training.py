from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import (
    ArchiveUploadCompleteOut,
    AutoTrainingJobCreateIn,
    AutoTrainingJobOut,
    MessageResponse,
    UploadChunkOut,
    UploadSessionCreateIn,
    UploadSessionOut,
)
from backend.app.services.archive_uploads import (
    ArchiveUploadError,
    complete_archive_upload_session,
    create_archive_upload_session,
    discard_archive_upload_session,
    get_archive_session_file,
    get_archive_session_payload_path,
    update_uploaded_archive_chunk,
)
from backend.app.services.auto_training import (
    create_auto_training_job,
    delete_all_archive_files,
    delete_archive_file_record,
    get_archive_file,
    list_archive_file_models,
    list_auto_training_jobs,
    register_uploaded_archives,
    serialize_archive_file,
)
from backend.app.services.tasks import dispatch_task
from cybersec_platform.contracts.api import ArchiveFileOut
from cybersec_platform.db import AutoTrainingJob, User

router = APIRouter(prefix="/auto-training", tags=["auto-training"])


async def _require_archive_file(session: SessionDep, archive_id: str):
    archive = await get_archive_file(session, archive_id)
    if archive is None:
        raise HTTPException(status_code=404, detail="Archive not found")
    return archive


@router.get("/archives", response_model=list[ArchiveFileOut], dependencies=[Depends(get_current_user)])
async def list_auto_training_archives(session: SessionDep) -> list[ArchiveFileOut]:
    archives = await list_archive_file_models(session)
    return [serialize_archive_file(item) for item in archives]


@router.delete("/archives/{archive_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def delete_auto_training_archive(archive_id: str, session: SessionDep) -> MessageResponse:
    archive = await _require_archive_file(session, archive_id)
    try:
        await delete_archive_file_record(session, archive)
        await session.commit()
    except ArchiveUploadError as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return MessageResponse(message=f"Archive deleted: {archive.name}")


@router.delete("/archives", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
async def clear_auto_training_archives(session: SessionDep) -> MessageResponse:
    try:
        deleted_count = await delete_all_archive_files(session)
        await session.commit()
    except ArchiveUploadError as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return MessageResponse(message=f"Deleted archives: {deleted_count}")


@router.post("/uploads/sessions", response_model=UploadSessionOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def init_archive_upload_session(payload: UploadSessionCreateIn) -> UploadSessionOut:
    try:
        session_payload = create_archive_upload_session([item.model_dump() for item in payload.files])
    except ArchiveUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return UploadSessionOut.model_validate(session_payload)


@router.put("/uploads/sessions/{session_id}/files/{file_id}", response_model=UploadChunkOut, dependencies=[Depends(get_current_user)])
async def upload_archive_chunk(session_id: str, file_id: str, request: Request) -> UploadChunkOut:
    try:
        session_payload = get_archive_session_file(session_id, file_id)
        file_payload = next(item for item in session_payload["files"] if item["file_id"] == file_id)
        offset = int(request.headers.get("X-Chunk-Offset", "-1"))
        chunk_length = int(request.headers.get("X-Chunk-Length", "-1"))
        if offset < 0 or chunk_length <= 0:
            raise ArchiveUploadError("Chunk offset and length are required")

        temp_path = get_archive_session_payload_path(session_id, file_payload["relative_path"])
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        current_size = temp_path.stat().st_size if temp_path.exists() else 0
        if current_size != file_payload["uploaded_bytes"] or offset != current_size:
            raise ArchiveUploadError(
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
            raise ArchiveUploadError(f"Invalid chunk length for {file_payload['relative_path']}")

        updated = update_uploaded_archive_chunk(session_id, file_id, offset + written)
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
    except ArchiveUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/uploads/sessions/{session_id}/complete", response_model=ArchiveUploadCompleteOut, dependencies=[Depends(get_current_user)])
async def finalize_archive_upload_session(session_id: str, session: SessionDep) -> ArchiveUploadCompleteOut:
    try:
        payload = complete_archive_upload_session(session_id)
        uploaded_records = await register_uploaded_archives(session, payload["uploaded_archives"])
        await session.commit()
        archives = [serialize_archive_file(item) for item in await list_archive_file_models(session)]
        return ArchiveUploadCompleteOut(
            session_id=payload["session_id"],
            status=payload["status"],
            uploaded_archives=[serialize_archive_file(item) for item in uploaded_records],
            archives=archives,
        )
    except ArchiveUploadError as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.delete("/uploads/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
async def discard_archive_upload(session_id: str) -> None:
    try:
        discard_archive_upload_session(session_id)
    except ArchiveUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/jobs", response_model=list[AutoTrainingJobOut], dependencies=[Depends(get_current_user)])
async def list_auto_training_job_records(session: SessionDep) -> list[AutoTrainingJobOut]:
    return [AutoTrainingJobOut.model_validate(item) for item in await list_auto_training_jobs(session)]


@router.get("/jobs/{job_id}", response_model=AutoTrainingJobOut, dependencies=[Depends(get_current_user)])
async def get_auto_training_job(job_id: str, session: SessionDep) -> AutoTrainingJobOut:
    item = await session.get(AutoTrainingJob, job_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Automatic training job not found")
    return AutoTrainingJobOut.model_validate(item)


@router.post("/jobs", response_model=AutoTrainingJobOut, status_code=status.HTTP_201_CREATED)
async def start_auto_training_job(
    session: SessionDep,
    payload: AutoTrainingJobCreateIn = Body(default_factory=AutoTrainingJobCreateIn),
    user: User = Depends(get_current_user),
) -> AutoTrainingJobOut:
    try:
        job = await create_auto_training_job(
            session,
            requested_by_user_id=user.id,
            archive_ids=payload.archive_ids,
        )
        record = await dispatch_task(
            session,
            task_name="training.run_auto_training",
            object_type="auto_training_job",
            object_id=job.id,
            queue="training",
            kwargs={"auto_training_job_id": job.id},
        )
        job.detail = {**job.detail, "task_id": record.id}
        await session.commit()
        await session.refresh(job)
        return AutoTrainingJobOut.model_validate(job)
    except ArchiveUploadError as exc:
        await session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
