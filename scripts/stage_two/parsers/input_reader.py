"""Safe input reading utilities for Stage Two parsers."""

from __future__ import annotations

import base64
import binascii
import bz2
import csv
import gzip
import io
import json
import lzma
import re
import struct
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Literal, TextIO

from config import (
    STAGE_TWO_MAX_BASE64_DECODE_BYTES,
    STAGE_TWO_MAX_ERROR_SAMPLES,
    STAGE_TWO_MAX_RAW_PREVIEW_BYTES,
    STAGE_TWO_TEXT_ENCODINGS,
)


InputReadMode = Literal[
    "text",
    "binary",
    "lines",
    "records",
    "json_lines",
    "csv_rows",
    "packet_bytes",
    "bson_stream",
]

DEFAULT_BINARY_CHUNK_SIZE = 64 * 1024
UTF8_BOM = b"\xef\xbb\xbf"
GZIP_MAGIC = b"\x1f\x8b"
BZ2_MAGIC = b"BZh"
XZ_MAGIC = b"\xfd7zXZ\x00"
ZIP_MAGIC_PREFIXES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
PCAP_MAGIC_PREFIXES = (
    b"\xd4\xc3\xb2\xa1",
    b"\xa1\xb2\xc3\xd4",
    b"\x4d\x3c\xb2\xa1",
    b"\xa1\xb2\x3c\x4d",
)
PCAPNG_MAGIC = b"\x0a\x0d\x0d\x0a"
BASE64_ALPHABET_PATTERN = re.compile(rb"^[A-Za-z0-9+/=\s]+$")
BASE64_PAYLOAD_KEYS: frozenset[str] = frozenset({"payload"})
TEXT_ENCODING_FALLBACKS: tuple[str, ...] = (
    "utf-8",
    "utf-8-sig",
    "cp1252",
    "latin-1",
    "ascii",
)


@dataclass
class ReaderMetadata:
    """Runtime metadata collected while a raw input file is read."""

    encoding_hint: str | None = None
    decode_error: str | None = None
    compression_hint: str | None = None
    base64_detected: bool = False
    decode_strategy: str = "plain"
    bytes_read: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class InputReaderError(ValueError):
    """Raised when an input reader mode cannot read the requested file safely."""


@dataclass(frozen=True)
class _TextDecodePlan:
    """Selected text decoding plan for one read operation."""

    encoding: str
    errors: str
    strategy: str
    decode_error: str | None = None
    warning: str | None = None


class _TrackedBinaryStream:
    """Small binary stream wrapper that updates ReaderMetadata.bytes_read."""

    def __init__(self, stream: BinaryIO, metadata: ReaderMetadata) -> None:
        self._stream = stream
        self._metadata = metadata

    def read(self, size: int = -1) -> bytes:
        data = self._stream.read(size)
        self._metadata.bytes_read += len(data)
        return data

    def readinto(self, buffer: bytearray | memoryview) -> int:
        bytes_read = self._stream.readinto(buffer)
        if bytes_read:
            self._metadata.bytes_read += bytes_read
        return 0 if bytes_read is None else bytes_read

    def seekable(self) -> bool:
        return self._stream.seekable()

    def readable(self) -> bool:
        return self._stream.readable()

    def tell(self) -> int:
        return self._stream.tell()

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self._stream:
            self._metadata.bytes_read += len(chunk)
            yield chunk

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)


class UniversalInputReader:
    """Common safe reader for text, structured text, and binary parser inputs."""

    def __init__(
        self,
        path: str | Path,
        *,
        encoding_hint: str | None = None,
        compression_hint: str | None = None,
        base64_detected: bool = False,
        decode_strategy: str = "plain",
    ) -> None:
        self.path = Path(path)
        self._base64_candidate_checked = False
        self._whole_file_base64_payload: bytes | None = None
        self.metadata = ReaderMetadata(
            encoding_hint=encoding_hint,
            compression_hint=compression_hint,
            base64_detected=base64_detected,
            decode_strategy=decode_strategy,
        )

    @contextmanager
    def open(self, mode: InputReadMode, **kwargs: Any) -> Iterator[Any]:
        """Open a supported read mode as a context-managed stream or iterator."""
        normalized_mode = mode.replace("-", "_")
        if normalized_mode == "text":
            with self.open_text(**kwargs) as stream:
                yield stream
            return
        if normalized_mode == "binary":
            with self.open_binary() as stream:
                yield stream
            return
        if normalized_mode == "lines":
            with self.iter_lines(**kwargs) as lines:
                yield lines
            return
        if normalized_mode == "records":
            with self.iter_records(**kwargs) as records:
                yield records
            return
        if normalized_mode == "json_lines":
            with self.iter_json_lines(**kwargs) as records:
                yield records
            return
        if normalized_mode == "csv_rows":
            with self.iter_csv_rows(**kwargs) as rows:
                yield rows
            return
        if normalized_mode == "packet_bytes":
            with self.iter_packet_bytes(**kwargs) as chunks:
                yield chunks
            return
        if normalized_mode == "bson_stream":
            with self.iter_bson_stream() as documents:
                yield documents
            return
        raise InputReaderError(f"unsupported input read mode: {mode}")

    @contextmanager
    def open_text(
        self,
        *,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = "",
    ) -> Iterator[TextIO]:
        """Open a text stream without loading the whole file into memory."""
        decode_plan = self._build_text_decode_plan(encoding=encoding, errors=errors)
        with self._open_binary_source() as binary_stream:
            stream = io.TextIOWrapper(
                binary_stream,
                encoding=decode_plan.encoding,
                errors=decode_plan.errors,
                newline=newline,
            )
            try:
                yield stream
            finally:
                stream.detach()

    @contextmanager
    def open_binary(self) -> Iterator[_TrackedBinaryStream]:
        """Open a tracked binary stream without text decoding."""
        with self._open_binary_source() as stream:
            yield _TrackedBinaryStream(stream, self.metadata)

    @contextmanager
    def iter_lines(
        self,
        *,
        encoding: str | None = None,
        errors: str | None = None,
        keepends: bool = True,
        skip_empty: bool = False,
    ) -> Iterator[Iterator[str]]:
        """Stream text lines from the file."""
        decode_plan = self._build_text_decode_plan(encoding=encoding, errors=errors)
        with self._open_binary_source() as binary_stream:
            stream = io.TextIOWrapper(
                binary_stream,
                encoding=decode_plan.encoding,
                errors=decode_plan.errors,
                newline="",
            )

            def line_iterator() -> Iterator[str]:
                for line in stream:
                    self._track_text_bytes(line, decode_plan.encoding)
                    line = self._maybe_decode_base64_line(line)
                    value = line if keepends else line.rstrip("\r\n")
                    if skip_empty and not value.strip():
                        continue
                    yield value

            try:
                yield line_iterator()
            finally:
                stream.detach()

    @contextmanager
    def iter_records(
        self,
        *,
        encoding: str | None = None,
        errors: str | None = None,
        skip_empty: bool = True,
    ) -> Iterator[Iterator[dict[str, Any]]]:
        """Stream generic line records while preserving record order."""
        with self.iter_lines(
            encoding=encoding,
            errors=errors,
            keepends=False,
            skip_empty=skip_empty,
        ) as lines:

            def record_iterator() -> Iterator[dict[str, Any]]:
                for index, line in enumerate(lines):
                    yield {"record_index": index, "raw": line}

            yield record_iterator()

    @contextmanager
    def iter_json_lines(
        self,
        *,
        encoding: str | None = None,
        errors: str | None = None,
        skip_empty: bool = True,
        strict: bool = True,
    ) -> Iterator[Iterator[Any]]:
        """Stream JSON-lines records without reading the full file."""
        with self.iter_lines(
            encoding=encoding,
            errors=errors,
            keepends=False,
            skip_empty=skip_empty,
        ) as lines:

            def json_iterator() -> Iterator[Any]:
                for line_number, line in enumerate(lines, start=1):
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        message = f"json line {line_number}: {exc.msg}"
                        self._record_error(message)
                        if strict:
                            raise InputReaderError(message) from exc
                        continue
                    yield self._decode_json_payload(record, line_number=line_number)

            yield json_iterator()

    @contextmanager
    def iter_csv_rows(
        self,
        *,
        encoding: str | None = None,
        errors: str | None = None,
        fieldnames: list[str] | tuple[str, ...] | None = None,
        dialect: str = "excel",
        **csv_options: Any,
    ) -> Iterator[Iterator[dict[str, Any]]]:
        """Stream CSV rows as dictionaries."""
        with self.iter_lines(
            encoding=encoding,
            errors=errors,
            keepends=True,
            skip_empty=False,
        ) as lines:
            reader = csv.DictReader(
                lines,
                fieldnames=fieldnames,
                dialect=dialect,
                **csv_options,
            )

            def row_iterator() -> Iterator[dict[str, Any]]:
                for row in reader:
                    yield dict(row)

            yield row_iterator()

    @contextmanager
    def iter_packet_bytes(
        self,
        *,
        chunk_size: int = DEFAULT_BINARY_CHUNK_SIZE,
    ) -> Iterator[Iterator[bytes]]:
        """Stream packet container bytes without decoding or parsing them."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        with self._open_binary_source() as stream:

            def chunk_iterator() -> Iterator[bytes]:
                while True:
                    chunk = stream.read(chunk_size)
                    if not chunk:
                        break
                    self.metadata.bytes_read += len(chunk)
                    yield chunk

            yield chunk_iterator()

    @contextmanager
    def iter_bson_stream(self) -> Iterator[Iterator[bytes]]:
        """Stream raw BSON document bytes using BSON length prefixes."""
        with self._open_binary_source() as stream:

            def document_iterator() -> Iterator[bytes]:
                document_index = 0
                while True:
                    prefix = stream.read(4)
                    if not prefix:
                        break
                    self.metadata.bytes_read += len(prefix)
                    if len(prefix) != 4:
                        message = f"bson document {document_index}: truncated length prefix"
                        self._record_error(message)
                        raise InputReaderError(message)
                    length = struct.unpack("<i", prefix)[0]
                    if length < 5:
                        message = f"bson document {document_index}: invalid document length {length}"
                        self._record_error(message)
                        raise InputReaderError(message)
                    payload = stream.read(length - 4)
                    self.metadata.bytes_read += len(payload)
                    if len(payload) != length - 4:
                        message = f"bson document {document_index}: truncated document payload"
                        self._record_error(message)
                        raise InputReaderError(message)
                    document_index += 1
                    yield prefix + payload

            yield document_iterator()

    @contextmanager
    def _open_binary_source(self) -> Iterator[BinaryIO]:
        base64_payload = self._get_whole_file_base64_payload()
        if base64_payload is not None:
            with io.BytesIO(base64_payload) as stream:
                with self._open_compressed_or_plain(stream, _read_preview(stream)) as source:
                    yield source
            return

        with self.path.open("rb") as stream:
            with self._open_compressed_or_plain(stream, _read_preview(stream)) as source:
                yield source

    @contextmanager
    def _open_compressed_or_plain(self, stream: BinaryIO, preview: bytes) -> Iterator[BinaryIO]:
        compression = _detect_compression(preview)
        self.metadata.compression_hint = compression
        if compression != "plain":
            self._append_decode_strategy(f"compression:{compression}")

        if compression == "gzip":
            with gzip.GzipFile(fileobj=stream, mode="rb") as gzip_stream:
                yield gzip_stream
            return
        if compression == "bz2":
            with bz2.BZ2File(stream, mode="rb") as bz2_stream:
                yield bz2_stream
            return
        if compression == "xz":
            with lzma.LZMAFile(stream, mode="rb") as lzma_stream:
                yield lzma_stream
            return
        if compression == "zip":
            with zipfile.ZipFile(stream) as archive:
                member = _select_safe_zip_member(archive)
                if member is None:
                    message = "zip archive has no safe regular file members"
                    self._record_error(message)
                    raise InputReaderError(message)
                safe_count = len([item for item in archive.infolist() if _is_safe_zip_member(item)])
                if safe_count > 1:
                    self._record_warning(
                        f"zip archive has {safe_count} safe members; reading first: {member.filename}"
                    )
                with archive.open(member, "r") as member_stream:
                    yield member_stream
            return

        yield stream

    def metadata_snapshot(self) -> ReaderMetadata:
        """Return a copy of current reader metadata."""
        return ReaderMetadata(
            encoding_hint=self.metadata.encoding_hint,
            decode_error=self.metadata.decode_error,
            compression_hint=self.metadata.compression_hint,
            base64_detected=self.metadata.base64_detected,
            decode_strategy=self.metadata.decode_strategy,
            bytes_read=self.metadata.bytes_read,
            warnings=list(self.metadata.warnings),
            errors=list(self.metadata.errors),
        )

    def _build_text_decode_plan(
        self,
        *,
        encoding: str | None,
        errors: str | None,
    ) -> _TextDecodePlan:
        explicit_encoding = encoding or self.metadata.encoding_hint
        preview = self._read_preview_bytes()
        if explicit_encoding:
            plan = _plan_explicit_encoding(
                preview,
                encoding=explicit_encoding,
                errors=errors,
            )
        else:
            plan = _detect_text_encoding(preview, errors=errors)
        self.metadata.encoding_hint = plan.encoding
        self._append_decode_strategy(f"text:{plan.strategy}")
        self.metadata.decode_error = plan.decode_error
        if plan.warning:
            self._record_warning(plan.warning)
        return plan

    def _read_preview_bytes(self) -> bytes:
        with self._open_binary_source() as stream:
            return stream.read(STAGE_TWO_MAX_RAW_PREVIEW_BYTES)

    def _get_whole_file_base64_payload(self) -> bytes | None:
        if self._base64_candidate_checked:
            return self._whole_file_base64_payload
        self._base64_candidate_checked = True
        try:
            file_size = self.path.stat().st_size
        except OSError as exc:
            self._record_error(f"failed to stat input file for base64 detection: {exc}")
            return None
        preview = self._read_raw_preview_bytes()
        if not _looks_like_base64_signal(preview):
            return None
        if not _looks_like_base64_candidate(preview):
            self._record_warning("whole-file base64 candidate failed strict validation")
            return None
        if file_size > _max_base64_encoded_bytes():
            self._record_warning(
                "whole-file base64 candidate skipped because encoded size exceeds safety limit"
            )
            return None
        raw = self.path.read_bytes()
        decoded = _decode_base64_bytes(raw)
        if decoded is None:
            self._record_warning("whole-file base64 candidate failed strict validation")
            return None
        if len(decoded) > STAGE_TWO_MAX_BASE64_DECODE_BYTES:
            self._record_warning("whole-file base64 candidate skipped because decoded size exceeds limit")
            return None
        if not _decoded_payload_looks_supported(decoded):
            self._record_warning("whole-file base64 candidate skipped because decoded payload type is unknown")
            return None
        self.metadata.base64_detected = True
        self._append_decode_strategy("base64:whole-file")
        self._whole_file_base64_payload = decoded
        return decoded

    def _read_raw_preview_bytes(self) -> bytes:
        with self.path.open("rb") as stream:
            return stream.read(STAGE_TWO_MAX_RAW_PREVIEW_BYTES)

    def _maybe_decode_base64_line(self, line: str) -> str:
        content, line_ending = _split_line_ending(line)
        if not content.strip():
            return line
        decoded = self._decode_base64_text_value(content, source="line")
        if decoded is None:
            return line
        if line_ending and not decoded.endswith(("\n", "\r")):
            return f"{decoded}{line_ending}"
        return decoded

    def _decode_json_payload(self, record: Any, *, line_number: int) -> Any:
        if not isinstance(record, dict):
            return record
        updated: dict[str, Any] | None = None
        for key in BASE64_PAYLOAD_KEYS:
            payload = record.get(key)
            if not isinstance(payload, str):
                continue
            decoded = self._decode_base64_text_value(payload, source=f"json {key} line {line_number}")
            if decoded is None:
                continue
            updated = dict(record) if updated is None else updated
            updated[key] = decoded
        return record if updated is None else updated

    def _decode_base64_text_value(self, value: str, *, source: str) -> str | None:
        try:
            encoded = value.strip().encode("ascii")
        except UnicodeEncodeError:
            return None
        if not _looks_like_base64_signal(encoded):
            return None
        if not _looks_like_base64_candidate(encoded):
            self._record_warning(f"{source} base64 candidate failed strict validation")
            return None
        if _estimated_base64_decoded_size(encoded) > STAGE_TWO_MAX_BASE64_DECODE_BYTES:
            self._record_warning(f"{source} base64 candidate skipped because decoded size exceeds limit")
            return None
        decoded = _decode_base64_bytes(encoded)
        if decoded is None:
            self._record_warning(f"{source} base64 candidate failed strict validation")
            return None
        if len(decoded) > STAGE_TWO_MAX_BASE64_DECODE_BYTES:
            self._record_warning(f"{source} base64 candidate skipped because decoded size exceeds limit")
            return None
        if not _decoded_payload_looks_supported(decoded):
            return None
        text = _decode_supported_text(decoded)
        if text is None:
            self._record_warning(f"{source} base64 candidate decoded to non-text payload")
            return None
        self.metadata.base64_detected = True
        self._append_decode_strategy(f"base64:{source}")
        return text

    def _append_decode_strategy(self, strategy: str) -> None:
        existing = [] if self.metadata.decode_strategy == "plain" else self.metadata.decode_strategy.split("|")
        if strategy not in existing:
            existing.append(strategy)
        self.metadata.decode_strategy = "|".join(existing) if existing else "plain"

    def _record_warning(self, message: str) -> None:
        if message not in self.metadata.warnings:
            self.metadata.warnings.append(message)

    def _record_error(self, message: str) -> None:
        if len(self.metadata.errors) < STAGE_TWO_MAX_ERROR_SAMPLES:
            self.metadata.errors.append(message)

    def _track_text_bytes(self, value: str, encoding: str) -> None:
        self.metadata.bytes_read += len(value.encode(encoding, errors="replace"))

    def _update_bytes_from_text_stream(self, stream: TextIO) -> None:
        try:
            byte_position = stream.buffer.tell()
        except (AttributeError, OSError, ValueError):
            return
        self.metadata.bytes_read = max(self.metadata.bytes_read, byte_position)


def _default_encoding() -> str:
    return STAGE_TWO_TEXT_ENCODINGS[0] if STAGE_TWO_TEXT_ENCODINGS else "utf-8"


def _read_preview(stream: BinaryIO) -> bytes:
    position = stream.tell() if stream.seekable() else None
    preview = stream.read(STAGE_TWO_MAX_RAW_PREVIEW_BYTES)
    if position is not None:
        stream.seek(position)
    return preview


def _detect_compression(preview: bytes) -> str:
    if preview.startswith(GZIP_MAGIC):
        return "gzip"
    if preview.startswith(BZ2_MAGIC):
        return "bz2"
    if preview.startswith(XZ_MAGIC):
        return "xz"
    if preview.startswith(ZIP_MAGIC_PREFIXES):
        return "zip"
    return "plain"


def _select_safe_zip_member(archive: zipfile.ZipFile) -> zipfile.ZipInfo | None:
    for member in archive.infolist():
        if _is_safe_zip_member(member):
            return member
    return None


def _is_safe_zip_member(member: zipfile.ZipInfo) -> bool:
    if member.is_dir():
        return False
    name = member.filename.replace("\\", "/")
    if not name or name.startswith("/") or ":" in name:
        return False
    parts = [part for part in name.split("/") if part]
    return bool(parts) and all(part != ".." for part in parts)


def _looks_like_base64_candidate(data: bytes) -> bool:
    stripped = b"".join(data.split())
    return _looks_like_base64_signal(stripped) and len(stripped) % 4 == 0


def _looks_like_base64_signal(data: bytes) -> bool:
    stripped = b"".join(data.split())
    return len(stripped) >= 8 and BASE64_ALPHABET_PATTERN.fullmatch(stripped) is not None


def _max_base64_encoded_bytes() -> int:
    return ((STAGE_TWO_MAX_BASE64_DECODE_BYTES + 2) // 3) * 4 + 4096


def _estimated_base64_decoded_size(data: bytes) -> int:
    stripped = b"".join(data.split())
    padding = stripped.count(b"=")
    return (len(stripped) * 3 // 4) - padding


def _decode_base64_bytes(data: bytes) -> bytes | None:
    stripped = b"".join(data.split())
    if not _looks_like_base64_candidate(stripped):
        return None
    try:
        return base64.b64decode(stripped, validate=True)
    except (binascii.Error, ValueError):
        return None


def _decoded_payload_looks_supported(data: bytes) -> bool:
    if not data:
        return False
    if _detect_compression(data) != "plain":
        return True
    if data.startswith((*PCAP_MAGIC_PREFIXES, PCAPNG_MAGIC)):
        return True
    if _looks_like_bson_document(data):
        return True
    return _decode_supported_text(data) is not None


def _looks_like_bson_document(data: bytes) -> bool:
    if len(data) < 5:
        return False
    length = struct.unpack("<i", data[:4])[0]
    return length == len(data) and data[-1:] == b"\x00"


def _decode_supported_text(data: bytes) -> str | None:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1", "ascii"):
        try:
            text = data.decode(encoding, errors="strict")
        except UnicodeDecodeError:
            continue
        if _looks_like_text_payload(text):
            return text
    return None


def _looks_like_text_payload(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    allowed_controls = {"\n", "\r", "\t"}
    printable_count = sum(1 for char in text if char.isprintable() or char in allowed_controls)
    if printable_count / max(len(text), 1) < 0.85:
        return False
    if stripped[0] in "{[":
        try:
            json.loads(stripped)
            return True
        except json.JSONDecodeError:
            pass
    return True


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1]
    return line, ""


def _encoding_candidates() -> tuple[str, ...]:
    candidates: list[str] = []
    for encoding in (*TEXT_ENCODING_FALLBACKS, *STAGE_TWO_TEXT_ENCODINGS):
        normalized = encoding.lower()
        if normalized not in candidates:
            candidates.append(normalized)
    return tuple(candidates)


def _detect_text_encoding(preview: bytes, *, errors: str | None) -> _TextDecodePlan:
    if preview.startswith(UTF8_BOM):
        strict_error = _strict_decode_error(preview, "utf-8-sig")
        if strict_error is None:
            return _TextDecodePlan(
                encoding="utf-8-sig",
                errors=errors or "strict",
                strategy="bom:utf-8-sig",
            )
        warning = f"UTF-8 BOM detected but strict decode failed; using replacement: {strict_error}"
        return _TextDecodePlan(
            encoding="utf-8-sig",
            errors=errors or "replace",
            strategy="bom:utf-8-sig:replace",
            decode_error=strict_error,
            warning=warning,
        )

    first_error: str | None = None
    failed_candidates: list[str] = []
    for candidate in _encoding_candidates():
        decode_error = _strict_decode_error(preview, candidate)
        if decode_error is None:
            if failed_candidates:
                warning = (
                    f"text decode fallback selected {candidate}; "
                    f"failed strict candidates: {', '.join(failed_candidates)}"
                )
                return _TextDecodePlan(
                    encoding=candidate,
                    errors=errors or "strict",
                    strategy="fallback:strict",
                    decode_error=first_error,
                    warning=warning,
                )
            return _TextDecodePlan(
                encoding=candidate,
                errors=errors or "strict",
                strategy="strict",
            )
        first_error = first_error or decode_error
        failed_candidates.append(candidate)

    decode_error = first_error or "no configured encoding could decode preview"
    return _TextDecodePlan(
        encoding=_default_encoding(),
        errors=errors or "replace",
        strategy="fallback:replace",
        decode_error=decode_error,
        warning=f"text decode fallback exhausted; using replacement: {decode_error}",
    )


def _plan_explicit_encoding(preview: bytes, *, encoding: str, errors: str | None) -> _TextDecodePlan:
    selected_errors = errors or "strict"
    if errors is not None:
        return _TextDecodePlan(
            encoding=encoding,
            errors=selected_errors,
            strategy=f"explicit:{selected_errors}",
        )
    decode_error = _strict_decode_error(preview, encoding)
    if decode_error is None:
        return _TextDecodePlan(
            encoding=encoding,
            errors="strict",
            strategy="explicit:strict",
        )
    return _TextDecodePlan(
        encoding=encoding,
        errors="replace",
        strategy="explicit:replace",
        decode_error=decode_error,
        warning=f"explicit encoding {encoding} failed strict preview decode; using replacement",
    )


def _strict_decode_error(data: bytes, encoding: str) -> str | None:
    try:
        data.decode(encoding, errors="strict")
    except UnicodeDecodeError as exc:
        return f"{encoding}: byte {exc.start}: {exc.reason}"
    except LookupError as exc:
        return f"{encoding}: {exc}"
    return None


def _csv_row_size_hint(row: dict[str, Any]) -> str:
    return ",".join("" if value is None else str(value) for value in row.values())
