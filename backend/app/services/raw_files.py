from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_platform.contracts.api import RawFileOut, ValidationStatus
from cybersec_platform.db import Dataset, RawFile
from cybersec_platform.ml.normalization import UnsupportedDatasetFormatError, detect_dataset_format

from backend.app.services.dataset_uploads import DatasetUploadError, get_raw_root, normalize_relative_path
from backend.app.services.managed_datasets import (
    count_managed_datasets_for_raw_file,
    has_managed_datasets,
    referenced_raw_file_ids,
)


def resolve_raw_absolute_path(relative_path: str) -> Path:
    normalized = normalize_relative_path(relative_path)
    root = get_raw_root().resolve()
    target = (root / Path(normalized)).resolve()
    if not target.is_relative_to(root):
        raise DatasetUploadError(f"Invalid relative path: {relative_path}")
    return target


def relative_path_from_absolute(path: str | Path) -> str:
    root = get_raw_root().resolve()
    target = Path(path).resolve()
    try:
        return target.relative_to(root).as_posix()
    except ValueError as exc:
        raise DatasetUploadError(f"Raw file is outside of the raw data root: {target}") from exc


def serialize_raw_file(raw_file: RawFile) -> RawFileOut:
    target = Path(raw_file.path)
    try:
        dataset_format = detect_dataset_format(target)
    except UnsupportedDatasetFormatError:
        dataset_format = target.suffix.lower().lstrip(".") or "unknown"

    modified_at = None
    if target.exists():
        stat = target.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC)

    return RawFileOut(
        id=raw_file.id,
        name=raw_file.name,
        path=raw_file.path,
        relative_path=relative_path_from_absolute(raw_file.path),
        size=raw_file.size,
        format=dataset_format,
        modified_at=modified_at,
    )


async def get_raw_file(session: AsyncSession, raw_file_id: str) -> RawFile | None:
    return await session.get(RawFile, raw_file_id)


async def get_raw_file_by_relative_path(session: AsyncSession, relative_path: str) -> RawFile | None:
    target = str(resolve_raw_absolute_path(relative_path))
    result = await session.execute(select(RawFile).where(RawFile.path == target))
    return result.scalar_one_or_none()


async def list_raw_file_models(session: AsyncSession) -> list[RawFile]:
    result = await session.execute(select(RawFile).order_by(RawFile.name.asc(), RawFile.id.asc()))
    return result.scalars().all()


async def sync_raw_file_records(session: AsyncSession) -> list[RawFile]:
    existing = {item.path: item for item in await list_raw_file_models(session)}
    discovered: dict[str, Path] = {}
    referenced_ids = await referenced_raw_file_ids(session)

    for path in sorted(get_raw_root().rglob("*")):
        if not path.is_file():
            continue
        try:
            detect_dataset_format(path)
        except UnsupportedDatasetFormatError:
            continue
        discovered[str(path.resolve())] = path.resolve()

    for path, raw_file in existing.items():
        if path not in discovered:
            if raw_file.id in referenced_ids:
                continue
            await session.delete(raw_file)

    for path, resolved in discovered.items():
        if path in existing:
            raw_file = existing[path]
            raw_file.name = resolved.name
            raw_file.size = resolved.stat().st_size
            continue
        session.add(RawFile(name=resolved.name, path=path, size=resolved.stat().st_size))

    await session.flush()
    return await list_raw_file_models(session)


async def ensure_raw_file_paths_available(session: AsyncSession, relative_paths: list[str]) -> None:
    absolute_paths = [str(resolve_raw_absolute_path(relative_path)) for relative_path in relative_paths]
    if not absolute_paths:
        return
    result = await session.execute(select(RawFile).where(RawFile.path.in_(absolute_paths)))
    existing = result.scalars().all()
    if existing:
        conflict = relative_path_from_absolute(existing[0].path)
        raise DatasetUploadError(f"Raw dataset file already exists: {conflict}", status_code=409)


async def register_uploaded_raw_files(session: AsyncSession, uploaded_files: list[dict]) -> list[RawFile]:
    records: list[RawFile] = []
    for payload in uploaded_files:
        target = resolve_raw_absolute_path(payload["relative_path"])
        record = RawFile(
            name=payload["file_name"],
            path=str(target),
            size=int(payload["size_bytes"]),
        )
        session.add(record)
        records.append(record)
    await session.flush()
    return records


def _reset_dataset_for_revalidation(dataset: Dataset) -> None:
    dataset.validation_status = ValidationStatus.PENDING.value
    dataset.validation_errors = {}
    dataset.normalized_path = None
    dataset.normalization_profile = None
    dataset.normalization_summary = {}
    dataset.normalization_report_path = None


def _mark_dataset_raw_source_deleted(dataset: Dataset) -> None:
    dataset.validation_status = ValidationStatus.FAILED.value
    dataset.validation_errors = {"error": "raw source deleted"}
    dataset.normalized_path = None
    dataset.normalization_profile = None
    dataset.normalization_summary = {}
    dataset.normalization_report_path = None


async def invalidate_datasets_for_raw_change(session: AsyncSession, raw_path: str) -> None:
    result = await session.execute(select(Dataset).where(Dataset.storage_path == raw_path))
    for dataset in result.scalars().all():
        _reset_dataset_for_revalidation(dataset)


async def invalidate_datasets_for_deleted_paths(session: AsyncSession, raw_paths: list[str]) -> None:
    if not raw_paths:
        return
    result = await session.execute(select(Dataset).where(Dataset.storage_path.in_(raw_paths)))
    for dataset in result.scalars().all():
        _mark_dataset_raw_source_deleted(dataset)


async def invalidate_all_datasets_for_raw_delete(session: AsyncSession) -> None:
    raw_root = get_raw_root().resolve()
    result = await session.execute(select(Dataset))
    for dataset in result.scalars().all():
        try:
            if Path(dataset.storage_path).resolve().is_relative_to(raw_root):
                _mark_dataset_raw_source_deleted(dataset)
        except OSError:
            continue


def _delete_path_if_exists(target: Path) -> None:
    if target.exists():
        target.unlink(missing_ok=True)
    current = target.parent
    raw_root = get_raw_root().resolve()
    while current != raw_root and current.exists():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


async def delete_raw_file_record(session: AsyncSession, raw_file: RawFile) -> None:
    reference_count = await count_managed_datasets_for_raw_file(session, raw_file.id)
    if reference_count > 0:
        raise DatasetUploadError("Raw file is referenced by registered datasets", status_code=409)
    await invalidate_datasets_for_deleted_paths(session, [raw_file.path])
    _delete_path_if_exists(Path(raw_file.path))
    await session.delete(raw_file)


async def delete_all_raw_files(session: AsyncSession) -> int:
    if await has_managed_datasets(session):
        raise DatasetUploadError("Raw files cannot be cleared while registered datasets exist", status_code=409)
    raw_files = await list_raw_file_models(session)
    deleted_count = len(raw_files)
    await invalidate_all_datasets_for_raw_delete(session)

    for raw_file in raw_files:
        _delete_path_if_exists(Path(raw_file.path))
        await session.delete(raw_file)

    raw_root = get_raw_root()
    for path in sorted(raw_root.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            try:
                path.rmdir()
            except OSError:
                continue

    return deleted_count
