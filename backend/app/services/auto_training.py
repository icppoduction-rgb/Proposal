from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_platform.contracts.api import ArchiveFileOut, JobStatus
from cybersec_platform.db import AutoTrainingArchive, AutoTrainingJob
from cybersec_platform.ml.auto_training import ArchiveExtractionError, detect_archive_format

from backend.app.services.archive_uploads import ArchiveUploadError, get_archive_root
from backend.app.services.dataset_uploads import normalize_relative_path


def resolve_archive_absolute_path(relative_path: str) -> Path:
    normalized = normalize_relative_path(relative_path)
    root = get_archive_root().resolve()
    target = (root / Path(normalized)).resolve()
    if not target.is_relative_to(root):
        raise ArchiveUploadError(f"Invalid archive path: {relative_path}")
    return target


def relative_archive_path_from_absolute(path: str | Path) -> str:
    root = get_archive_root().resolve()
    target = Path(path).resolve()
    try:
        return target.relative_to(root).as_posix()
    except ValueError as exc:
        raise ArchiveUploadError(f"Archive is outside of the archive root: {target}") from exc


def serialize_archive_file(item: AutoTrainingArchive) -> ArchiveFileOut:
    archive_path = Path(item.path)
    try:
        archive_format = detect_archive_format(archive_path)
    except ArchiveExtractionError:
        archive_format = archive_path.suffix.lower().lstrip(".") or "unknown"
    return ArchiveFileOut(
        id=item.id,
        name=item.name,
        path=item.path,
        relative_path=item.relative_path,
        size=item.size,
        format=archive_format,
        created_at=item.created_at,
    )


async def get_archive_file(session: AsyncSession, archive_id: str) -> AutoTrainingArchive | None:
    return await session.get(AutoTrainingArchive, archive_id)


async def list_archive_file_models(session: AsyncSession) -> list[AutoTrainingArchive]:
    result = await session.execute(select(AutoTrainingArchive).order_by(AutoTrainingArchive.name.asc(), AutoTrainingArchive.id.asc()))
    return result.scalars().all()


async def sync_archive_records(session: AsyncSession) -> list[AutoTrainingArchive]:
    existing = {item.path: item for item in await list_archive_file_models(session)}
    discovered: dict[str, Path] = {}

    for path in sorted(get_archive_root().rglob("*")):
        if not path.is_file():
            continue
        try:
            detect_archive_format(path)
        except ArchiveExtractionError:
            continue
        discovered[str(path.resolve())] = path.resolve()

    for path, archive in existing.items():
        if path not in discovered:
            await session.delete(archive)

    for path, resolved in discovered.items():
        if path in existing:
            archive = existing[path]
            archive.name = resolved.name
            archive.size = resolved.stat().st_size
            archive.relative_path = resolved.relative_to(get_archive_root().resolve()).as_posix()
            continue
        session.add(
            AutoTrainingArchive(
                name=resolved.name,
                path=path,
                relative_path=resolved.relative_to(get_archive_root().resolve()).as_posix(),
                size=resolved.stat().st_size,
            )
        )

    await session.flush()
    return await list_archive_file_models(session)


async def register_uploaded_archives(session: AsyncSession, uploaded_archives: list[dict]) -> list[AutoTrainingArchive]:
    resolved_payloads: list[tuple[dict, Path]] = []
    archive_paths: set[str] = set()
    relative_paths: set[str] = set()

    for payload in uploaded_archives:
        target = resolve_archive_absolute_path(payload["relative_path"])
        resolved_payloads.append((payload, target))
        archive_paths.add(str(target))
        relative_paths.add(payload["relative_path"])

    existing_by_path: dict[str, AutoTrainingArchive] = {}
    existing_by_relative_path: dict[str, AutoTrainingArchive] = {}
    if archive_paths or relative_paths:
        result = await session.execute(
            select(AutoTrainingArchive).where(
                or_(
                    AutoTrainingArchive.path.in_(archive_paths),
                    AutoTrainingArchive.relative_path.in_(relative_paths),
                )
            )
        )
        for item in result.scalars().all():
            existing_by_path[item.path] = item
            existing_by_relative_path[item.relative_path] = item

    records: list[AutoTrainingArchive] = []
    for payload, target in resolved_payloads:
        path = str(target)
        record = existing_by_path.get(path) or existing_by_relative_path.get(payload["relative_path"])
        if record is not None:
            record.name = payload["file_name"]
            record.path = path
            record.relative_path = payload["relative_path"]
            record.size = int(payload["size_bytes"])
            records.append(record)
            continue

        record = AutoTrainingArchive(
            name=payload["file_name"],
            path=path,
            relative_path=payload["relative_path"],
            size=int(payload["size_bytes"]),
        )
        session.add(record)
        records.append(record)
    await session.flush()
    return records


async def has_active_auto_training_jobs(session: AsyncSession) -> bool:
    result = await session.execute(
        select(func.count())
        .select_from(AutoTrainingJob)
        .where(AutoTrainingJob.status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value]))
    )
    return bool(result.scalar_one())


def _delete_path_if_exists(target: Path) -> None:
    if target.exists():
        target.unlink(missing_ok=True)
    current = target.parent
    archive_root = get_archive_root().resolve()
    while current != archive_root and current.exists():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


async def delete_archive_file_record(session: AsyncSession, archive: AutoTrainingArchive) -> None:
    if await has_active_auto_training_jobs(session):
        raise ArchiveUploadError("Archives cannot be removed while automatic training is running", status_code=409)
    _delete_path_if_exists(Path(archive.path))
    await session.delete(archive)


async def delete_all_archive_files(session: AsyncSession) -> int:
    if await has_active_auto_training_jobs(session):
        raise ArchiveUploadError("Archives cannot be cleared while automatic training is running", status_code=409)
    archives = await list_archive_file_models(session)
    deleted_count = len(archives)
    for archive in archives:
        _delete_path_if_exists(Path(archive.path))
        await session.delete(archive)
    archive_root = get_archive_root()
    for path in sorted(archive_root.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            try:
                path.rmdir()
            except OSError:
                continue
    return deleted_count


async def list_auto_training_jobs(session: AsyncSession) -> list[AutoTrainingJob]:
    result = await session.execute(select(AutoTrainingJob).order_by(AutoTrainingJob.created_at.desc(), AutoTrainingJob.id.desc()))
    return result.scalars().all()


async def create_auto_training_job(
    session: AsyncSession,
    *,
    requested_by_user_id: str | None,
    archive_ids: list[str] | None = None,
) -> AutoTrainingJob:
    if await has_active_auto_training_jobs(session):
        raise ArchiveUploadError("Automatic training is already running", status_code=409)

    archives = await list_archive_file_models(session)
    if archive_ids:
        selected = [archive for archive in archives if archive.id in set(archive_ids)]
    else:
        selected = archives

    if not selected:
        raise ArchiveUploadError("At least one uploaded archive is required", status_code=400)
    if archive_ids and len(selected) != len(set(archive_ids)):
        raise ArchiveUploadError("One or more selected archives were not found", status_code=404)

    job = AutoTrainingJob(
        requested_by_user_id=requested_by_user_id,
        archive_ids=[archive.id for archive in selected],
        detail={
            "archive_count": len(selected),
            "archive_names": [archive.name for archive in selected],
        },
    )
    session.add(job)
    await session.flush()
    return job
