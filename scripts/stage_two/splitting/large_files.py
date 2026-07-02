"""Split large line-oriented raw files into catalog-ready chunks."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import PATH_FOLDER_DATASETS_FILTER
from scripts.db.models import Dataset, DatasetFile
from scripts.db.models.constants import ACTIVE_CATALOG_SOURCE_GROUP, ACTIVE_DATASET_ROLE_VALUES, BRANCH_VALUES
from scripts.db.repositories import DatasetFileRepository
from scripts.stage_two.catalog_exclusions import is_excluded_dataset_file


HeaderMode = Literal["auto", "yes", "no"]

LINE_SPLIT_SOURCE_FORMATS: frozenset[str] = frozenset(
    {
        "csv",
        "pcap.csv",
        "txt",
        "json",
        "json-1",
        "log",
        "log-1",
        "log-2",
        "log-3",
        "auth.log",
        "syslog",
        "syslog.log",
        "syslog-1",
        "syslog-2",
        "syslog-3",
        "syslog-4",
        "mainlog",
        "mainlog-1",
        "mainlog-2",
        "mainlog-3",
        "messages",
        "messages-1",
        "mail-info-1",
        "mail-warn-1",
        "journal",
        "journal~",
        "info",
        "ghc",
        "sc",
        "netflow_day",
        "netflow_ids",
        "wls_day",
        "cpu.log",
        "diskio.log",
        "filesystem.log",
        "fsstat.log",
        "load.log",
        "memory.log",
        "network.log",
        "process.log",
        "process.summary.log",
        "service.log",
        "socket.summary.log",
        "uptime.log",
    }
)

BINARY_SOURCE_FORMATS: frozenset[str] = frozenset({"cap", "pcap", "pcapng", "bson"})


@dataclass(frozen=True)
class SplitLargeFilesRequest:
    """Selection and execution options for splitting large Stage Two raw files."""

    branch: str
    role: str
    source_format: str
    max_part_size_bytes: int
    min_file_size_bytes: int
    limit: int | None = None
    apply_changes: bool = False
    register: bool = False
    overwrite: bool = False
    keep_source_ready: bool = False
    header_mode: HeaderMode = "auto"


@dataclass(frozen=True)
class SplitFileResult:
    """Result for one source file split attempt."""

    file_id: int | None
    file_path: str
    status: str
    source_size_bytes: int | None
    output_dir: str | None
    chunks_created: int
    rows_written: int
    bytes_written: int
    registered: int = 0
    source_status: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class SplitLargeFilesResult:
    """Batch result for split-large-files."""

    status: str
    branch: str
    role: str
    source_format: str
    selected: int
    split: int
    skipped: int
    failed: int
    chunks_created: int
    registered: int
    files: tuple[SplitFileResult, ...]


@dataclass(frozen=True)
class _ChunkInfo:
    path: Path
    rows_written: int
    bytes_written: int
    byte_start: int | None
    byte_end: int | None
    line_start: int | None
    line_end: int | None
    chunk_hash_sha256: str


@dataclass(frozen=True)
class _SplitPlan:
    output_dir: Path
    has_header: bool
    existing_parts: tuple[Path, ...]


class SplitLargeFilesService:
    """Split large catalog files into line-aligned chunks."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.file_repository = DatasetFileRepository(session)

    def split_large_files(self, request: SplitLargeFilesRequest) -> SplitLargeFilesResult:
        """Split matching large files and optionally register chunks in the catalog."""
        _validate_request(request)
        files = self._selected_files(request)
        results: list[SplitFileResult] = []
        for file in files:
            try:
                results.append(self._split_one(file, request))
            except Exception as exc:
                results.append(
                    SplitFileResult(
                        file_id=file.id,
                        file_path=file.file_path,
                        status="FAILED",
                        source_size_bytes=file.file_size_bytes,
                        output_dir=None,
                        chunks_created=0,
                        rows_written=0,
                        bytes_written=0,
                        error=_exception_message(exc),
                    )
                )

        failed = sum(1 for result in results if result.status == "FAILED")
        split = sum(1 for result in results if result.status == "SPLIT")
        skipped = sum(1 for result in results if result.status.startswith("SKIPPED"))
        status = "SUCCESS" if failed == 0 else ("FAILED" if split == 0 else "PARTIAL_SUCCESS")
        return SplitLargeFilesResult(
            status=status,
            branch=request.branch,
            role=request.role,
            source_format=request.source_format,
            selected=len(files),
            split=split,
            skipped=skipped,
            failed=failed,
            chunks_created=sum(result.chunks_created for result in results),
            registered=sum(result.registered for result in results),
            files=tuple(results),
        )

    def _selected_files(self, request: SplitLargeFilesRequest) -> list[DatasetFile]:
        statement = (
            select(DatasetFile)
            .join(Dataset)
            .where(
                Dataset.source_group == ACTIVE_CATALOG_SOURCE_GROUP,
                DatasetFile.branch == request.branch,
                DatasetFile.role == request.role,
                DatasetFile.source_format == request.source_format,
                DatasetFile.status == "READY_FOR_PARSING",
            )
            .order_by(DatasetFile.id)
        )
        if request.min_file_size_bytes > 0:
            statement = statement.where(DatasetFile.file_size_bytes >= request.min_file_size_bytes)
        files = list(self.session.execute(statement).scalars())
        filtered_files = [
            file
            for file in files
            if not _is_chunk_path(Path(file.file_path)) and not is_excluded_dataset_file(file)
        ]
        return filtered_files[: request.limit] if request.limit is not None else filtered_files

    def _split_one(self, file: DatasetFile, request: SplitLargeFilesRequest) -> SplitFileResult:
        path = Path(file.file_path)
        if request.source_format in BINARY_SOURCE_FORMATS or request.source_format not in LINE_SPLIT_SOURCE_FORMATS:
            return SplitFileResult(
                file_id=file.id,
                file_path=file.file_path,
                status="SKIPPED_UNSUPPORTED_FORMAT",
                source_size_bytes=file.file_size_bytes,
                output_dir=None,
                chunks_created=0,
                rows_written=0,
                bytes_written=0,
                error=f"source_format is not line-splittable: {request.source_format}",
            )
        if not path.exists():
            return SplitFileResult(
                file_id=file.id,
                file_path=file.file_path,
                status="FAILED",
                source_size_bytes=file.file_size_bytes,
                output_dir=None,
                chunks_created=0,
                rows_written=0,
                bytes_written=0,
                error="source file does not exist",
            )

        plan = _build_split_plan(path, request)
        if plan.existing_parts and not request.overwrite:
            return SplitFileResult(
                file_id=file.id,
                file_path=file.file_path,
                status="SKIPPED_EXISTING_PARTS",
                source_size_bytes=file.file_size_bytes,
                output_dir=str(plan.output_dir),
                chunks_created=len(plan.existing_parts),
                rows_written=0,
                bytes_written=sum(part.stat().st_size for part in plan.existing_parts if part.exists()),
                error="output parts already exist; pass --overwrite to recreate",
            )
        if not request.apply_changes:
            planned_parts = _planned_part_count(path, request.max_part_size_bytes)
            return SplitFileResult(
                file_id=file.id,
                file_path=file.file_path,
                status="DRY_RUN",
                source_size_bytes=file.file_size_bytes,
                output_dir=str(plan.output_dir),
                chunks_created=planned_parts,
                rows_written=0,
                bytes_written=0,
            )

        chunks = _split_line_file(
            path,
            output_dir=plan.output_dir,
            max_part_size_bytes=request.max_part_size_bytes,
            has_header=plan.has_header,
            overwrite=request.overwrite,
        )
        registered = 0
        source_status = file.status
        if request.register:
            registered = self._register_chunks(file, chunks, request)
            if chunks and registered == len(chunks) and not request.keep_source_ready:
                self.file_repository.mark_file_status(
                    file,
                    "SKIPPED",
                    error_message=f"split into {len(chunks)} chunks under {plan.output_dir}",
                )
                source_status = file.status

        return SplitFileResult(
            file_id=file.id,
            file_path=file.file_path,
            status="SPLIT",
            source_size_bytes=file.file_size_bytes,
            output_dir=str(plan.output_dir),
            chunks_created=len(chunks),
            rows_written=sum(chunk.rows_written for chunk in chunks),
            bytes_written=sum(chunk.bytes_written for chunk in chunks),
            registered=registered,
            source_status=source_status,
        )

    def _register_chunks(
        self,
        source_file: DatasetFile,
        chunks: list[_ChunkInfo],
        request: SplitLargeFilesRequest,
    ) -> int:
        rows: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        root = Path(PATH_FOLDER_DATASETS_FILTER).expanduser().resolve()
        for index, chunk in enumerate(chunks, start=1):
            try:
                relative_path = chunk.path.resolve().relative_to(root)
            except ValueError:
                relative_path = chunk.path.name  # type: ignore[assignment]
            chunk_id = f"{source_file.id}:{index}"
            rows.append(
                {
                    "dataset_id": source_file.dataset_id,
                    "ingestion_run_id": None,
                    "file_path": str(chunk.path),
                    "relative_path": str(relative_path),
                    "file_name": chunk.path.name,
                    "file_extension": chunk.path.suffix.lower() or None,
                    "source_format": request.source_format,
                    "file_size_bytes": chunk.path.stat().st_size,
                    "file_hash_sha256": chunk.chunk_hash_sha256,
                    "file_modified_at": now,
                    "role": source_file.role,
                    "branch": source_file.branch,
                    "status": "READY_FOR_PARSING",
                    "row_count_hint": chunk.rows_written,
                    "metadata_json": {
                        "chunk_id": chunk_id,
                        "parent_file_id": source_file.id,
                        "chunk_index": index,
                        "chunk_path": str(chunk.path),
                        "byte_start": chunk.byte_start,
                        "byte_end": chunk.byte_end,
                        "line_start": chunk.line_start,
                        "line_end": chunk.line_end,
                        "chunk_hash_sha256": chunk.chunk_hash_sha256,
                        "source_order_preserved": True,
                        "original_source_path": source_file.file_path,
                        "split_source_file_id": source_file.id,
                        "split_source_file_path": source_file.file_path,
                        "split_part_index": index,
                        "split_part_count": len(chunks),
                        "split_max_part_size_bytes": request.max_part_size_bytes,
                        "root_path": PATH_FOLDER_DATASETS_FILTER,
                        "root_relative_path": str(relative_path),
                    },
                }
            )
        return self.file_repository.bulk_upsert_files(rows, force_status=True)


def _validate_request(request: SplitLargeFilesRequest) -> None:
    if request.branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"split-large-files branch must be one of: {allowed}")
    if request.role not in ACTIVE_DATASET_ROLE_VALUES:
        allowed = ", ".join(ACTIVE_DATASET_ROLE_VALUES)
        raise ValueError(f"split-large-files role must be one of: {allowed}")
    if not request.source_format:
        raise ValueError("split-large-files format must not be empty")
    if request.max_part_size_bytes <= 0:
        raise ValueError("split-large-files max part size must be positive")
    if request.min_file_size_bytes < 0:
        raise ValueError("split-large-files min file size must be non-negative")
    if request.register and not request.apply_changes:
        raise ValueError("split-large-files --register requires --apply")


def _build_split_plan(path: Path, request: SplitLargeFilesRequest) -> _SplitPlan:
    output_dir = _chunk_output_dir(path)
    existing_parts = tuple(sorted(output_dir.glob(_part_glob(path)))) if output_dir.exists() else ()
    return _SplitPlan(
        output_dir=output_dir,
        has_header=_detect_header(path, request.source_format, request.header_mode),
        existing_parts=existing_parts,
    )


def _chunk_output_dir(path: Path) -> Path:
    root = Path(PATH_FOLDER_DATASETS_FILTER).expanduser().resolve()
    try:
        relative = path.resolve().relative_to(root)
        return root / "chunked" / relative.parent / f"{path.name}.parts"
    except ValueError:
        return path.parent / f"{path.name}.parts"


def _part_glob(path: Path) -> str:
    suffix = path.suffix
    base = path.name[: -len(suffix)] if suffix else path.name
    return f"{base}.part-*{suffix}"


def _part_path(path: Path, output_dir: Path, part_index: int) -> Path:
    suffix = path.suffix
    base = path.name[: -len(suffix)] if suffix else path.name
    return output_dir / f"{base}.part-{part_index:06d}{suffix}"


def _split_line_file(
    path: Path,
    *,
    output_dir: Path,
    max_part_size_bytes: int,
    has_header: bool,
    overwrite: bool,
) -> list[_ChunkInfo]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if overwrite:
        for part in output_dir.glob(_part_glob(path)):
            if part.is_file():
                part.unlink()

    chunks: list[_ChunkInfo] = []
    part_index = 0
    output_file: Any | None = None
    output_path: Path | None = None
    tmp_path: Path | None = None
    chunk_byte_start: int | None = None
    chunk_line_start: int | None = None
    last_byte_end: int | None = None
    last_line_number: int | None = None
    rows_written = 0
    bytes_written = 0
    current_size = 0

    def close_part() -> None:
        nonlocal output_file, output_path, tmp_path
        nonlocal chunk_byte_start, chunk_line_start, last_byte_end, last_line_number
        nonlocal rows_written, bytes_written, current_size
        if output_file is None or output_path is None or tmp_path is None:
            return
        output_file.close()
        tmp_path.replace(output_path)
        chunks.append(
            _ChunkInfo(
                path=output_path,
                rows_written=rows_written,
                bytes_written=bytes_written,
                byte_start=chunk_byte_start,
                byte_end=last_byte_end,
                line_start=chunk_line_start,
                line_end=last_line_number,
                chunk_hash_sha256=_sha256_file(output_path),
            )
        )
        output_file = None
        output_path = None
        tmp_path = None
        chunk_byte_start = None
        chunk_line_start = None
        last_byte_end = None
        last_line_number = None
        rows_written = 0
        bytes_written = 0
        current_size = 0

    def open_part(header: bytes | None, *, byte_start: int, line_start: int) -> None:
        nonlocal part_index, output_file, output_path, tmp_path, current_size
        nonlocal chunk_byte_start, chunk_line_start
        part_index += 1
        output_path = _part_path(path, output_dir, part_index)
        tmp_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
        output_file = tmp_path.open("wb")
        chunk_byte_start = byte_start
        chunk_line_start = line_start
        current_size = 0
        if header:
            output_file.write(header)
            current_size += len(header)

    with path.open("rb") as input_file:
        header = input_file.readline() if has_header else None
        line_number = 1 if has_header else 0
        while True:
            line_start_byte = input_file.tell()
            line = input_file.readline()
            if not line:
                break
            line_number += 1
            if output_file is None:
                open_part(header, byte_start=line_start_byte, line_start=line_number)
            elif rows_written > 0 and current_size + len(line) > max_part_size_bytes:
                close_part()
                open_part(header, byte_start=line_start_byte, line_start=line_number)
            output_file.write(line)
            rows_written += 1
            bytes_written += len(line)
            current_size += len(line)
            last_byte_end = line_start_byte + len(line)
            last_line_number = line_number
        close_part()

    return chunks


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _planned_part_count(path: Path, max_part_size_bytes: int) -> int:
    try:
        size = path.stat().st_size
    except OSError:
        return 0
    return max(1, (size + max_part_size_bytes - 1) // max_part_size_bytes)


def _detect_header(path: Path, source_format: str, header_mode: HeaderMode) -> bool:
    if header_mode == "yes":
        return True
    if header_mode == "no":
        return False
    if source_format == "pcap.csv":
        return True
    if source_format != "csv":
        return False
    try:
        sample = path.read_text(encoding="utf-8", errors="replace")[:65536]
    except OSError:
        return False
    try:
        return csv.Sniffer().has_header(sample)
    except csv.Error:
        first_line = sample.splitlines()[0] if sample.splitlines() else ""
        lowered = first_line.lower()
        return any(token in lowered for token in ("domain", "timestamp", "label", "src", "dst", "qtype"))


def _is_chunk_path(path: Path) -> bool:
    return ".part-" in path.name or path.parent.name.endswith(".parts")


def _exception_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or type(exc).__name__
