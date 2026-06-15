"""Safe input reading utilities for Stage Two parsers."""

from __future__ import annotations

import csv
import json
import struct
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Literal, TextIO

from config import (
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
        with self.path.open(
            "r",
            encoding=decode_plan.encoding,
            errors=decode_plan.errors,
            newline=newline,
        ) as stream:
            yield stream
            self._update_bytes_from_text_stream(stream)

    @contextmanager
    def open_binary(self) -> Iterator[_TrackedBinaryStream]:
        """Open a tracked binary stream without text decoding."""
        with self.path.open("rb") as stream:
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
        with self.path.open(
            "r",
            encoding=decode_plan.encoding,
            errors=decode_plan.errors,
            newline="",
        ) as stream:

            def line_iterator() -> Iterator[str]:
                for line in stream:
                    self._track_text_bytes(line, decode_plan.encoding)
                    value = line if keepends else line.rstrip("\r\n")
                    if skip_empty and not value.strip():
                        continue
                    yield value

            yield line_iterator()

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
                        yield json.loads(line)
                    except json.JSONDecodeError as exc:
                        message = f"json line {line_number}: {exc.msg}"
                        self._record_error(message)
                        if strict:
                            raise InputReaderError(message) from exc

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
        decode_plan = self._build_text_decode_plan(encoding=encoding, errors=errors)
        with self.path.open(
            "r",
            encoding=decode_plan.encoding,
            errors=decode_plan.errors,
            newline="",
        ) as stream:
            reader = csv.DictReader(
                stream,
                fieldnames=fieldnames,
                dialect=dialect,
                **csv_options,
            )

            def row_iterator() -> Iterator[dict[str, Any]]:
                for row in reader:
                    self._track_text_bytes(_csv_row_size_hint(row), decode_plan.encoding)
                    yield dict(row)

            yield row_iterator()
            self._update_bytes_from_text_stream(stream)

    @contextmanager
    def iter_packet_bytes(
        self,
        *,
        chunk_size: int = DEFAULT_BINARY_CHUNK_SIZE,
    ) -> Iterator[Iterator[bytes]]:
        """Stream packet container bytes without decoding or parsing them."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        with self.path.open("rb") as stream:

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
        with self.path.open("rb") as stream:

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
        self.metadata.decode_strategy = plan.strategy
        self.metadata.decode_error = plan.decode_error
        if plan.warning:
            self._record_warning(plan.warning)
        return plan

    def _read_preview_bytes(self) -> bytes:
        with self.path.open("rb") as stream:
            return stream.read(STAGE_TWO_MAX_RAW_PREVIEW_BYTES)

    def _record_warning(self, message: str) -> None:
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
