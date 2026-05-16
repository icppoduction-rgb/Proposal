from __future__ import annotations

import argparse
import base64
import binascii
import csv
import gzip
import hashlib
import json
import os
import re
import sys
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from scripts.read_format import (
    DEFAULT_TEXT_ENCODINGS,
    PCAP_MAGIC_HEADERS,
    TEXT_EXTENSIONS,
)


HOST_SPLITS = ("TRAIN", "VALIDATION", "EXPERIMENTS", "TEST")
JSON_EXTENSIONS = {".json", ".jsonl", ".ndjson"}
CSV_EXTENSIONS = {".csv"}
GZIP_EXTENSIONS = {".gz"}
ZIP_EXTENSIONS = {".docx", ".odt", ".pptx", ".xlsx"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
PDF_EXTENSIONS = {".pdf"}
PCAP_EXTENSIONS = {".pcap", ".pcapng", ".cap"}
NPZ_EXTENSIONS = {".npz"}

DEFAULT_TEXT_PREVIEW_BYTES = 1024 * 1024
DEFAULT_BINARY_PREVIEW_BYTES = 64 * 1024
DEFAULT_JSON_PARSE_LIMIT_BYTES = 8 * 1024 * 1024
DEFAULT_CSV_ROW_LIMIT = 10_000
DEFAULT_JSONL_ROW_LIMIT = 10_000
DEFAULT_STRING_PREVIEW_CHARS = 4096
DEFAULT_PROGRESS_INTERVAL = 1000


class HostConversionError(Exception):
    """Base exception for host dataset conversion errors."""


@dataclass(frozen=True)
class HostConversionConfig:
    """Runtime limits that keep conversion reproducible on very large datasets."""

    source_root: Path
    target_root: Path
    splits: tuple[str, ...] = HOST_SPLITS
    text_preview_bytes: int = DEFAULT_TEXT_PREVIEW_BYTES
    binary_preview_bytes: int = DEFAULT_BINARY_PREVIEW_BYTES
    json_parse_limit_bytes: int = DEFAULT_JSON_PARSE_LIMIT_BYTES
    csv_row_limit: int = DEFAULT_CSV_ROW_LIMIT
    jsonl_row_limit: int = DEFAULT_JSONL_ROW_LIMIT
    string_preview_chars: int = DEFAULT_STRING_PREVIEW_CHARS
    workers: int = 1
    overwrite: bool = True
    progress_interval: int = DEFAULT_PROGRESS_INTERVAL


@dataclass(frozen=True)
class ConvertedFileResult:
    """Single-file conversion result used for summary counters and diagnostics."""

    source_path: str
    target_path: str
    split: str
    dataset: str
    status: str
    data_type: str
    size_bytes: int
    error: str | None = None


@dataclass
class HostConversionSummary:
    """Aggregated conversion report written after all files are processed."""

    source_root: str
    target_root: str
    total_files: int = 0
    converted_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    total_source_bytes: int = 0
    by_split: dict[str, int] = field(default_factory=dict)
    by_type: dict[str, int] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)


def iter_host_files(source_root: Path, splits: Iterable[str]) -> Iterable[Path]:
    """Yields every file under datasets/host/<split> in deterministic order."""

    for split in splits:
        split_dir = source_root / split
        if not split_dir.exists():
            continue
        if not split_dir.is_dir():
            raise NotADirectoryError(f"Host split path is not a directory: {split_dir}")

        yield from sorted(path for path in split_dir.rglob("*") if path.is_file())


def convert_host_datasets(config: HostConversionConfig) -> HostConversionSummary:
    """Converts all configured host splits into datasets-new/host JSON files."""

    source_root = config.source_root.resolve()
    target_root = config.target_root.resolve()

    if not source_root.exists():
        raise FileNotFoundError(f"Host datasets directory not found: {source_root}")
    if not source_root.is_dir():
        raise NotADirectoryError(f"Host datasets path is not a directory: {source_root}")

    for split in config.splits:
        (target_root / split).mkdir(parents=True, exist_ok=True)

    files = list(iter_host_files(source_root=source_root, splits=config.splits))
    summary = HostConversionSummary(
        source_root=str(source_root),
        target_root=str(target_root),
        total_files=len(files),
    )

    print(f"Host files discovered: {len(files)}")
    if config.workers <= 1:
        results = _convert_sequential(files, source_root, config)
    else:
        results = _convert_parallel(files, source_root, config)

    _fill_summary(summary=summary, results=results)
    _write_summary(target_root=target_root, summary=summary)
    return summary


def _convert_sequential(
    files: list[Path],
    source_root: Path,
    config: HostConversionConfig,
) -> list[ConvertedFileResult]:
    """Runs conversion in the current thread; useful for debugging and tests."""

    results: list[ConvertedFileResult] = []

    for index, path in enumerate(files, start=1):
        results.append(convert_one_file(path=path, source_root=source_root, config=config))
        _print_progress(index=index, total=len(files), config=config)

    return results


def _convert_parallel(
    files: list[Path],
    source_root: Path,
    config: HostConversionConfig,
) -> list[ConvertedFileResult]:
    """Runs file conversion with a bounded thread pool for IO-heavy workloads."""

    results: list[ConvertedFileResult] = []

    with ThreadPoolExecutor(max_workers=config.workers) as executor:
        futures = [
            executor.submit(convert_one_file, path, source_root, config)
            for path in files
        ]

        for index, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            _print_progress(index=index, total=len(files), config=config)

    return results


def convert_one_file(
    path: Path,
    source_root: Path,
    config: HostConversionConfig,
) -> ConvertedFileResult:
    """Reads one source file, normalizes it, and writes one target JSON file."""

    split = extract_split(path=path, source_root=source_root)
    dataset = extract_dataset_name(path=path, source_root=source_root)
    target_path = build_output_path(path=path, source_root=source_root, target_root=config.target_root)
    size_bytes = path.stat().st_size if path.exists() else 0

    if target_path.exists() and not config.overwrite:
        return ConvertedFileResult(
            source_path=str(path),
            target_path=str(target_path),
            split=split,
            dataset=dataset,
            status="skipped",
            data_type="skipped",
            size_bytes=size_bytes,
        )

    try:
        data = read_host_file(path=path, source_root=source_root, config=config)
        write_json_atomic(target_path, {"data": data})
        return ConvertedFileResult(
            source_path=str(path),
            target_path=str(target_path),
            split=split,
            dataset=dataset,
            status="converted",
            data_type=str(data.get("type", "unknown")),
            size_bytes=size_bytes,
        )
    except Exception as error:
        error_payload = build_error_payload(
            path=path,
            source_root=source_root,
            error=error,
        )
        write_json_atomic(target_path, {"data": error_payload})
        return ConvertedFileResult(
            source_path=str(path),
            target_path=str(target_path),
            split=split,
            dataset=dataset,
            status="failed",
            data_type="error",
            size_bytes=size_bytes,
            error=f"{type(error).__name__}: {error}",
        )


def read_host_file(path: Path, source_root: Path, config: HostConversionConfig) -> dict[str, Any]:
    """Selects a bounded reader based on extension and lightweight content sniffing."""

    metadata = build_metadata(path=path, source_root=source_root)
    extension = path.suffix.lower()
    sample = read_prefix(path, min(config.binary_preview_bytes, 8192))

    # PCAP and binary-like formats are handled before generic text sniffing.
    if is_pcap_path(path):
        return read_pcap_preview(path=path, metadata=metadata, config=config)
    if extension in PDF_EXTENSIONS:
        return read_pdf_preview(path=path, metadata=metadata, config=config)
    if extension in IMAGE_EXTENSIONS:
        return read_image_preview(path=path, metadata=metadata, config=config)
    if extension in NPZ_EXTENSIONS:
        return read_npz_metadata(path=path, metadata=metadata)
    if extension in GZIP_EXTENSIONS:
        return read_gzip_preview(path=path, metadata=metadata, config=config)
    if extension in ZIP_EXTENSIONS:
        return read_zip_metadata(path=path, metadata=metadata)
    if extension in JSON_EXTENSIONS:
        return read_json_or_preview(path=path, metadata=metadata, config=config)
    if extension in CSV_EXTENSIONS:
        return read_csv_preview(path=path, metadata=metadata, config=config)

    # Extensionless LANL files are JSONL or CSV; detect them from the first line.
    if sample_looks_like_json_line(sample):
        return read_jsonl_preview(path=path, metadata=metadata, config=config)
    if not extension and sample_looks_like_csv(sample):
        return read_csv_preview(path=path, metadata=metadata, config=config)

    if extension in TEXT_EXTENSIONS or is_text_like(sample):
        return read_text_preview(path=path, metadata=metadata, config=config)

    return read_binary_preview(path=path, metadata=metadata, config=config)


def read_json_or_preview(path: Path, metadata: dict[str, Any], config: HostConversionConfig) -> dict[str, Any]:
    """Parses small JSON files and falls back to a text preview for huge JSON reports."""

    size_bytes = int(metadata["size_bytes"])
    if size_bytes > config.json_parse_limit_bytes:
        result = read_text_preview(path=path, metadata=metadata, config=config)
        result["type"] = "json_preview"
        result["metadata"] |= {
            "parsed": False,
            "parse_skipped_reason": "file is larger than json_parse_limit_bytes",
            "json_parse_limit_bytes": config.json_parse_limit_bytes,
        }
        return result

    content, encoding, truncated = read_text_with_limit(path=path, limit_bytes=config.json_parse_limit_bytes + 1)
    if truncated:
        raise HostConversionError(f"JSON file unexpectedly exceeded parse limit: {path}")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        rows = parse_json_lines_from_text(content=content, config=config)
        if rows is not None:
            return {
                "type": "jsonl",
                "metadata": metadata | {"encoding": encoding, "parsed": True, "rows_returned": len(rows)},
                "content": rows,
            }

        result = read_text_preview(path=path, metadata=metadata, config=config)
        result["type"] = "json"
        result["metadata"] |= {"parsed": False}
        return result

    return {
        "type": "json",
        "metadata": metadata
        | {
            "encoding": encoding,
            "parsed": True,
            "content_normalized_for_human_readability": True,
        },
        "content": normalize_json_value(parsed, config=config),
    }


def read_jsonl_preview(path: Path, metadata: dict[str, Any], config: HostConversionConfig) -> dict[str, Any]:
    """Reads JSON Lines with a row limit so large LANL streams stay manageable."""

    encoding = detect_text_encoding(read_prefix(path, 8192))
    rows: list[Any] = []
    rows_seen = 0

    with path.open("r", encoding=encoding, errors="replace", newline="") as stream:
        for line in stream:
            stripped = line.strip()
            if not stripped:
                continue

            row = json.loads(stripped)
            if rows_seen < config.jsonl_row_limit:
                rows.append(normalize_json_value(row, config=config))

            rows_seen += 1
            if rows_seen > config.jsonl_row_limit:
                break

    return {
        "type": "jsonl",
        "metadata": metadata
        | {
            "encoding": encoding,
            "parsed": True,
            "rows_returned": len(rows),
            "rows_scanned": rows_seen,
            "rows_truncated": rows_seen > len(rows),
            "row_limit": config.jsonl_row_limit,
            "content_normalized_for_human_readability": True,
        },
        "content": rows,
    }


def read_csv_preview(path: Path, metadata: dict[str, Any], config: HostConversionConfig) -> dict[str, Any]:
    """Reads CSV rows with header detection and a stable row limit."""

    sample = read_prefix(path, 64 * 1024)
    encoding = detect_text_encoding(sample)
    sample_text = sample.decode(encoding, errors="replace")
    set_max_csv_field_size()

    try:
        dialect = csv.Sniffer().sniff(sample_text)
    except csv.Error:
        dialect = csv.excel

    has_header = detect_csv_header(sample_text)
    rows: list[dict[str, Any]] = []
    rows_seen = 0
    fieldnames: list[str] = []

    with path.open("r", encoding=encoding, errors="replace", newline="") as stream:
        if has_header:
            reader = csv.DictReader(stream, dialect=dialect)
            fieldnames = list(reader.fieldnames or [])
            for row in reader:
                if rows_seen < config.csv_row_limit:
                    rows.append(dict(row))
                rows_seen += 1
                if rows_seen > config.csv_row_limit:
                    break
        else:
            reader = csv.reader(stream, dialect=dialect)
            for row in reader:
                if not fieldnames:
                    fieldnames = [f"column_{index}" for index in range(len(row))]
                if rows_seen < config.csv_row_limit:
                    rows.append(row_to_dict(row=row, fieldnames=fieldnames))
                rows_seen += 1
                if rows_seen > config.csv_row_limit:
                    break

    return {
        "type": "csv",
        "metadata": metadata
        | {
            "encoding": encoding,
            "has_header": has_header,
            "rows_returned": len(rows),
            "rows_scanned": rows_seen,
            "rows_truncated": rows_seen > len(rows),
            "row_limit": config.csv_row_limit,
            "columns": fieldnames,
        },
        "content": rows,
    }


def read_text_preview(path: Path, metadata: dict[str, Any], config: HostConversionConfig) -> dict[str, Any]:
    """Reads full text for small files and a human-readable preview for large files."""

    content, encoding, truncated = read_text_with_limit(path=path, limit_bytes=config.text_preview_bytes + 1)
    if truncated:
        content = content[: config.text_preview_bytes]

    return {
        "type": "text",
        "metadata": metadata
        | {
            "encoding": encoding,
            "content_truncated": truncated,
            "preview_limit_bytes": config.text_preview_bytes,
        },
        "content": content,
    }


def read_binary_preview(
    path: Path,
    metadata: dict[str, Any],
    config: HostConversionConfig,
    *,
    data_type: str = "binary",
) -> dict[str, Any]:
    """Converts binary bytes into human-readable previews instead of raw base64."""

    preview = read_prefix(path, config.binary_preview_bytes)
    source_bytes = int(metadata["size_bytes"])

    return {
        "type": data_type,
        "metadata": metadata
        | {
            "preview_bytes": len(preview),
            "content_truncated": len(preview) < source_bytes,
            "content_base64_included": False,
            "preview_limit_bytes": config.binary_preview_bytes,
        },
        "decoded_content": decoded_binary_preview(payload=preview, source_bytes=source_bytes),
    }


def read_pcap_preview(path: Path, metadata: dict[str, Any], config: HostConversionConfig) -> dict[str, Any]:
    """Reads PCAP headers and byte previews without loading huge captures fully."""

    result = read_binary_preview(path=path, metadata=metadata, config=config, data_type="pcap")
    preview = read_prefix(path, config.binary_preview_bytes)
    result["format"] = "pcap"
    result["metadata"] |= parse_pcap_preview_metadata(preview)
    return result


def read_pdf_preview(path: Path, metadata: dict[str, Any], config: HostConversionConfig) -> dict[str, Any]:
    """Adds a PDF header preview to the generic binary representation."""

    result = read_binary_preview(path=path, metadata=metadata, config=config, data_type="pdf")
    sample = read_prefix(path, 256)
    result["pdf"] = {
        "header": sample[:32].splitlines()[0].decode("latin-1", errors="replace") if sample else "",
    }
    return result


def read_image_preview(path: Path, metadata: dict[str, Any], config: HostConversionConfig) -> dict[str, Any]:
    """Adds basic PNG/JPEG dimensions when they are available in the header."""

    result = read_binary_preview(path=path, metadata=metadata, config=config, data_type="image")
    sample = read_prefix(path, 1024 * 1024)
    result["image"] = parse_image_dimensions(sample, path.suffix.lower())
    return result


def read_gzip_preview(path: Path, metadata: dict[str, Any], config: HostConversionConfig) -> dict[str, Any]:
    """Streams a bounded decompressed gzip preview."""

    with gzip.open(path, "rb") as stream:
        payload = stream.read(config.text_preview_bytes + 1)

    truncated = len(payload) > config.text_preview_bytes
    preview = payload[: config.text_preview_bytes]

    if is_text_like(preview):
        encoding = detect_text_encoding(preview)
        return {
            "type": "gzip",
            "metadata": metadata
            | {
                "encoding": encoding,
                "decompressed_preview_bytes": len(preview),
                "decompressed_truncated": truncated,
            },
            "content": preview.decode(encoding, errors="replace"),
        }

    return {
        "type": "gzip",
        "metadata": metadata
        | {
            "decompressed_preview_bytes": len(preview),
            "decompressed_truncated": truncated,
            "content_base64_included": False,
        },
        "decoded_content": decoded_binary_preview(payload=preview, source_bytes=int(metadata["size_bytes"])),
    }


def read_zip_metadata(path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Reads ZIP/OOXML member metadata and extracts common document text."""

    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        content = extract_zip_document_content(archive=archive, extension=path.suffix.lower())

    return {
        "type": path.suffix.lower().lstrip(".") or "zip",
        "metadata": metadata | {"members": members, "members_count": len(members)},
        "content": content if content is not None else {"members": members},
    }


def read_npz_metadata(path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Reads NumPy .npz container metadata without importing numpy."""

    arrays: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            if not member.endswith(".npy"):
                continue
            with archive.open(member) as file:
                magic = file.read(6)
                version = tuple(file.read(2))
                arrays.append({"name": member, "magic": magic.decode("latin-1"), "version": version})

    return {
        "type": "npz",
        "metadata": metadata,
        "content": {"arrays": arrays},
    }


def build_metadata(path: Path, source_root: Path) -> dict[str, Any]:
    """Builds common metadata that mirrors datasets-new/dns and adds host split context."""

    relative_path = path.resolve().relative_to(source_root.resolve())
    relative_parts = relative_path.parts
    return {
        "path": str(path),
        "relative_path": str(relative_path),
        "name": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "split": relative_parts[0] if relative_parts else "",
        "dataset": relative_parts[1] if len(relative_parts) > 1 else "",
    }


def build_error_payload(path: Path, source_root: Path, error: Exception) -> dict[str, Any]:
    """Creates a JSON record even when a source file cannot be parsed."""

    metadata = build_metadata(path=path, source_root=source_root)
    return {
        "type": "error",
        "metadata": metadata,
        "error": {
            "class": type(error).__name__,
            "message": str(error),
        },
    }


def build_output_path(path: Path, source_root: Path, target_root: Path) -> Path:
    """Maps a source file to a flat unique JSON filename under its split directory."""

    relative_path = path.resolve().relative_to(source_root.resolve())
    split = relative_path.parts[0]
    safe_stem = sanitize_filename(path.stem or path.name)
    digest = hashlib.sha1(str(relative_path).encode("utf-8")).hexdigest()[:12]
    return target_root / split / f"{safe_stem}__{digest}.json"


def sanitize_filename(value: str, max_length: int = 120) -> str:
    """Converts arbitrary dataset filenames into safe flat JSON output names."""

    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    if not normalized:
        normalized = "dataset_file"
    return normalized[:max_length]


def extract_split(path: Path, source_root: Path) -> str:
    """Extracts TRAIN/VALIDATION/EXPERIMENTS/TEST from a source path."""

    parts = path.resolve().relative_to(source_root.resolve()).parts
    return parts[0] if parts else ""


def extract_dataset_name(path: Path, source_root: Path) -> str:
    """Extracts the dataset folder name under a host split."""

    parts = path.resolve().relative_to(source_root.resolve()).parts
    return parts[1] if len(parts) > 1 else ""


def read_prefix(path: Path, size: int) -> bytes:
    """Reads only a file prefix to avoid loading multi-gigabyte datasets into memory."""

    with path.open("rb") as stream:
        return stream.read(size)


def read_text_with_limit(path: Path, limit_bytes: int) -> tuple[str, str, bool]:
    """Reads a bounded text payload and returns text, encoding, and truncation flag."""

    payload = read_prefix(path, limit_bytes)
    truncated = len(payload) == limit_bytes and path.stat().st_size >= limit_bytes
    if truncated:
        payload = payload[:-1]

    encoding = detect_text_encoding(payload)
    return payload.decode(encoding, errors="replace"), encoding, truncated


def detect_text_encoding(payload: bytes) -> str:
    """Finds the first configured encoding that can decode a byte sample."""

    for encoding in DEFAULT_TEXT_ENCODINGS:
        # Python's utf-16 decoder requires a BOM. Without this guard, short
        # ASCII-like CSV samples can be misdetected and fail during streaming.
        if encoding == "utf-16" and not payload.startswith((b"\xff\xfe", b"\xfe\xff")):
            continue
        try:
            payload.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def is_text_like(payload: bytes) -> bool:
    """Checks whether bytes are likely human-readable text."""

    if not payload:
        return True

    sample = payload[:8192]
    if sample.count(b"\x00") / max(len(sample), 1) > 0.05:
        return False

    encoding = detect_text_encoding(sample)
    text = sample.decode(encoding, errors="replace")
    control_chars = sum(
        1
        for char in text
        if ord(char) < 32 and char not in "\r\n\t\f\b"
    )
    return control_chars / max(len(text), 1) < 0.10


def sample_looks_like_json_line(sample: bytes) -> bool:
    """Detects JSON Lines from the first non-empty line."""

    if not sample:
        return False

    encoding = detect_text_encoding(sample)
    text = sample.decode(encoding, errors="replace")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith(("{", "[")):
            return False
        try:
            json.loads(stripped)
            return True
        except json.JSONDecodeError:
            return False

    return False


def sample_looks_like_csv(sample: bytes) -> bool:
    """Detects simple delimited text for extensionless LANL netflow files."""

    if not sample:
        return False

    encoding = detect_text_encoding(sample)
    text = sample.decode(encoding, errors="replace")
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if not first_line:
        return False

    return any(separator in first_line for separator in (",", "\t", ";"))


def parse_json_lines_from_text(content: str, config: HostConversionConfig) -> list[Any] | None:
    """Parses JSON Lines content when regular JSON parsing fails."""

    rows: list[Any] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if len(rows) < config.jsonl_row_limit:
            rows.append(normalize_json_value(row, config=config))
    return rows if rows else None


def normalize_json_value(value: Any, config: HostConversionConfig, key: str = "", depth: int = 0) -> Any:
    """Normalizes nested JSON, decoding base64 fields and shortening binary-like strings."""

    if depth > 40:
        return {"type": "max_depth_preview", "repr": repr(value)[: config.string_preview_chars]}

    if isinstance(value, dict):
        return {
            clean_text_for_json(str(item_key)): normalize_json_value(
                item_value,
                config=config,
                key=str(item_key),
                depth=depth + 1,
            )
            for item_key, item_value in value.items()
        }

    if isinstance(value, list):
        return [
            normalize_json_value(item, config=config, key=key, depth=depth + 1)
            for item in value
        ]

    if isinstance(value, str):
        if should_decode_base64_field(key=key, value=value):
            return decode_base64_string(value=value, config=config)
        if should_preview_string(value=value, config=config):
            return preview_string(value=value, config=config)
        return clean_text_for_json(value)

    return value


def should_decode_base64_field(key: str, value: str) -> bool:
    """Returns True for explicit base64 fields, avoiding accidental decoding of normal text."""

    normalized_key = key.lower()
    if "base64" not in normalized_key and not normalized_key.endswith("_b64"):
        return False
    if len(value) < 16:
        return False

    compact = "".join(value.split())
    if len(compact) % 4 != 0:
        return False

    try:
        base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        return False

    return True


def decode_base64_string(value: str, config: HostConversionConfig) -> dict[str, Any]:
    """Decodes a base64 string into readable previews and omits the raw bulky payload."""

    compact = "".join(value.split())
    decoded = base64.b64decode(compact, validate=True)
    preview = decoded[: config.binary_preview_bytes]
    return {
        "encoding": "base64",
        "source_chars": len(value),
        "decoded": decoded_binary_preview(payload=preview, source_bytes=len(decoded)),
    }


def should_preview_string(value: str, config: HostConversionConfig) -> bool:
    """Finds very long or binary-like strings that would make JSON unreadable."""

    if len(value) > config.string_preview_chars:
        return True

    if not value:
        return False

    control_chars = sum(
        1
        for char in value
        if ord(char) < 32 and char not in "\r\n\t\f\b"
    )
    return control_chars / max(len(value), 1) > 0.05


def preview_string(value: str, config: HostConversionConfig) -> dict[str, Any]:
    """Builds a readable representation for long or control-character-heavy strings."""

    preview = value[: config.string_preview_chars]
    return {
        "type": "string_preview",
        "source_chars": len(value),
        "truncated": len(value) > len(preview),
        "preview": clean_text_for_json(sanitize_text_preview(preview)),
    }


def sanitize_text_preview(value: str) -> str:
    """Replaces non-printable characters with spaces while preserving line breaks and tabs."""

    return "".join(
        char if (ord(char) >= 32 or char in "\r\n\t") else " "
        for char in value
    )


def clean_text_for_json(value: str) -> str:
    """Replaces lone UTF-16 surrogates that cannot be encoded as UTF-8 JSON."""

    return value.encode("utf-8", errors="replace").decode("utf-8")


def decoded_binary_preview(payload: bytes, source_bytes: int) -> dict[str, Any]:
    """Creates a readable view of binary data that replaces raw content_base64."""

    result: dict[str, Any] = {
        "source_bytes": source_bytes,
        "preview_bytes": len(payload),
        "preview_hex": payload.hex(" "),
        "preview_ascii": format_ascii(payload),
    }

    if is_text_like(payload):
        encoding = detect_text_encoding(payload)
        result["text_preview"] = clean_text_for_json(payload.decode(encoding, errors="replace"))
        result["text_encoding"] = encoding

    return result


def format_ascii(payload: bytes) -> str:
    """Formats bytes as printable ASCII, replacing binary bytes with dots."""

    return "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in payload)


def is_pcap_path(path: Path) -> bool:
    """Detects classic PCAP/PCAPNG files and rotated files named log.pcap.<timestamp>."""

    extension = path.suffix.lower()
    return extension in PCAP_EXTENSIONS or ".pcap." in path.name.lower()


def parse_pcap_preview_metadata(payload: bytes) -> dict[str, Any]:
    """Parses only capture header metadata that is available in the bounded preview."""

    if len(payload) < 4:
        return {"pcap_header_parsed": False}

    if payload[:4] == b"\x0a\x0d\x0d\x0a":
        return {
            "pcap_header_parsed": True,
            "pcap_type": "pcapng",
            "magic_hex": payload[:4].hex(),
        }

    parser = PCAP_MAGIC_HEADERS.get(payload[:4])
    if parser is None or len(payload) < 24:
        return {
            "pcap_header_parsed": False,
            "magic_hex": payload[:4].hex(),
        }

    byte_order, timestamp_precision = parser
    import struct

    version_major, version_minor, _thiszone, _sigfigs, snaplen, network = struct.unpack(
        f"{byte_order}HHIIII",
        payload[4:24],
    )
    return {
        "pcap_header_parsed": True,
        "pcap_type": "pcap",
        "magic_hex": payload[:4].hex(),
        "version": f"{version_major}.{version_minor}",
        "snaplen": snaplen,
        "network": network,
        "timestamp_precision": timestamp_precision,
    }


def parse_image_dimensions(payload: bytes, extension: str) -> dict[str, int] | None:
    """Parses PNG and JPEG dimensions from file headers."""

    if extension == ".png" and payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 24:
        import struct

        width, height = struct.unpack(">II", payload[16:24])
        return {"width": width, "height": height}

    if extension in {".jpg", ".jpeg"} and payload.startswith(b"\xff\xd8"):
        return parse_jpeg_dimensions(payload)

    return None


def parse_jpeg_dimensions(payload: bytes) -> dict[str, int] | None:
    """Finds JPEG Start Of Frame marker and returns image dimensions."""

    import struct

    offset = 2
    while offset + 9 < len(payload):
        if payload[offset] != 0xFF:
            offset += 1
            continue

        marker = payload[offset + 1]
        length = struct.unpack(">H", payload[offset + 2:offset + 4])[0]
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            height, width = struct.unpack(">HH", payload[offset + 5:offset + 9])
            return {"width": width, "height": height}

        offset += 2 + length

    return None


def extract_zip_document_content(archive: zipfile.ZipFile, extension: str) -> dict[str, Any] | None:
    """Extracts readable text from common Office/OpenDocument containers."""

    from xml.etree import ElementTree

    try:
        if extension == ".docx" and "word/document.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("word/document.xml"))
            text = "\n".join(node.text for node in root.iter() if node.tag.endswith("}t") and node.text)
            return {"text": text}

        if extension == ".odt" and "content.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("content.xml"))
            text = "\n".join(text.strip() for text in root.itertext() if text.strip())
            return {"text": text}

        if extension == ".pptx":
            slides = []
            for member in sorted(name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                root = ElementTree.fromstring(archive.read(member))
                text = "\n".join(node.text for node in root.iter() if node.tag.endswith("}t") and node.text)
                slides.append({"name": member, "text": text})
            return {"slides": slides}

        if extension == ".xlsx":
            sheets = [
                member
                for member in archive.namelist()
                if member.startswith("xl/worksheets/sheet") and member.endswith(".xml")
            ]
            return {"worksheets": sorted(sheets)}
    except (KeyError, ElementTree.ParseError):
        return None

    return None


def detect_csv_header(sample: str) -> bool:
    """Runs csv.Sniffer header detection with a conservative fallback."""

    try:
        return csv.Sniffer().has_header(sample)
    except csv.Error:
        return True


def set_max_csv_field_size() -> None:
    """Raises CSV field limit to support large cells from security telemetry."""

    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit //= 10


def row_to_dict(row: list[str], fieldnames: list[str]) -> dict[str, Any]:
    """Converts a headerless CSV row into a stable object shape."""

    normalized = {
        field: row[index] if index < len(row) else None
        for index, field in enumerate(fieldnames)
    }
    if len(row) > len(fieldnames):
        normalized["_extra"] = row[len(fieldnames):]
    return normalized


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    """Writes JSON via a temporary file so partial outputs are not left behind."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temp_path.replace(path)


def _fill_summary(summary: HostConversionSummary, results: list[ConvertedFileResult]) -> None:
    """Aggregates per-file results into compact split/type counters."""

    by_split: Counter[str] = Counter()
    by_type: Counter[str] = Counter()
    errors: list[dict[str, str]] = []
    total_source_bytes = 0
    converted_files = 0
    skipped_files = 0
    failed_files = 0

    for result in results:
        total_source_bytes += result.size_bytes
        by_split[result.split] += 1
        by_type[result.data_type] += 1

        if result.status == "converted":
            converted_files += 1
        elif result.status == "skipped":
            skipped_files += 1
        elif result.status == "failed":
            failed_files += 1
            errors.append(
                {
                    "source_path": result.source_path,
                    "target_path": result.target_path,
                    "error": result.error or "",
                }
            )

    summary.converted_files = converted_files
    summary.skipped_files = skipped_files
    summary.failed_files = failed_files
    summary.total_source_bytes = total_source_bytes
    summary.by_split = dict(sorted(by_split.items()))
    summary.by_type = dict(sorted(by_type.items()))
    summary.errors = errors[:1000]


def _write_summary(target_root: Path, summary: HostConversionSummary) -> None:
    """Writes the final conversion summary next to split output directories."""

    write_json_atomic(
        target_root / "conversion_summary.json",
        {
            "source_root": summary.source_root,
            "target_root": summary.target_root,
            "total_files": summary.total_files,
            "converted_files": summary.converted_files,
            "skipped_files": summary.skipped_files,
            "failed_files": summary.failed_files,
            "total_source_bytes": summary.total_source_bytes,
            "by_split": summary.by_split,
            "by_type": summary.by_type,
            "errors": summary.errors,
        },
    )


def _print_progress(index: int, total: int, config: HostConversionConfig) -> None:
    """Prints bounded progress updates for long conversion runs."""

    if config.progress_interval <= 0:
        return
    if index == total or index % config.progress_interval == 0:
        print(f"Converted {index}/{total} host files")


def print_host_conversion_summary(summary: HostConversionSummary) -> None:
    """Prints a concise CLI report after conversion."""

    print(f"Source: {summary.source_root}")
    print(f"Target: {summary.target_root}")
    print(f"Total files: {summary.total_files}")
    print(f"Converted files: {summary.converted_files}")
    print(f"Skipped files: {summary.skipped_files}")
    print(f"Failed files: {summary.failed_files}")
    print(f"Total source bytes: {summary.total_source_bytes}")
    print("By split:")
    for split, count in summary.by_split.items():
        print(f" - {split}: {count}")
    print("By type:")
    for data_type, count in summary.by_type.items():
        print(f" - {data_type}: {count}")


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for standalone host conversion."""

    parser = argparse.ArgumentParser(description="Convert datasets/host files into datasets-new/host JSON files.")
    parser.add_argument("--source", default=r"datasets\host", help="Path to datasets/host")
    parser.add_argument("--target", default=r"datasets-new\host", help="Path to datasets-new/host")
    parser.add_argument(
        "--split",
        action="append",
        choices=HOST_SPLITS,
        help="Host split to convert. Can be passed multiple times. Defaults to all splits.",
    )
    parser.add_argument("--workers", type=int, default=max(1, min((os.cpu_count() or 1), 4)))
    parser.add_argument("--text-preview-bytes", type=int, default=DEFAULT_TEXT_PREVIEW_BYTES)
    parser.add_argument("--binary-preview-bytes", type=int, default=DEFAULT_BINARY_PREVIEW_BYTES)
    parser.add_argument("--json-parse-limit-bytes", type=int, default=DEFAULT_JSON_PARSE_LIMIT_BYTES)
    parser.add_argument("--csv-row-limit", type=int, default=DEFAULT_CSV_ROW_LIMIT)
    parser.add_argument("--jsonl-row-limit", type=int, default=DEFAULT_JSONL_ROW_LIMIT)
    parser.add_argument("--no-overwrite", action="store_true", help="Skip target JSON files that already exist")
    return parser.parse_args()


def main() -> None:
    """Runs host dataset conversion from CLI."""

    args = parse_args()
    config = HostConversionConfig(
        source_root=Path(args.source),
        target_root=Path(args.target),
        splits=tuple(args.split or HOST_SPLITS),
        text_preview_bytes=args.text_preview_bytes,
        binary_preview_bytes=args.binary_preview_bytes,
        json_parse_limit_bytes=args.json_parse_limit_bytes,
        csv_row_limit=args.csv_row_limit,
        jsonl_row_limit=args.jsonl_row_limit,
        workers=args.workers,
        overwrite=not args.no_overwrite,
    )
    summary = convert_host_datasets(config)
    print_host_conversion_summary(summary)


if __name__ == "__main__":
    main()
