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


@dataclass
class ReaderMetadata:
    """Runtime metadata collected while a raw input file is read."""

    encoding_hint: str | None = None
    compression_hint: str | None = None
    base64_detected: bool = False
    decode_strategy: str = "plain"
    bytes_read: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class InputReaderError(ValueError):
    """Raised when an input reader mode cannot read the requested file safely."""


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
            encoding_hint=encoding_hint or _default_encoding(),
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
        errors: str = "replace",
        newline: str | None = "",
    ) -> Iterator[TextIO]:
        """Open a text stream without loading the whole file into memory."""
        selected_encoding = encoding or self.metadata.encoding_hint or _default_encoding()
        self.metadata.encoding_hint = selected_encoding
        with self.path.open("r", encoding=selected_encoding, errors=errors, newline=newline) as stream:
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
        errors: str = "replace",
        keepends: bool = True,
        skip_empty: bool = False,
    ) -> Iterator[Iterator[str]]:
        """Stream text lines from the file."""
        selected_encoding = encoding or self.metadata.encoding_hint or _default_encoding()
        self.metadata.encoding_hint = selected_encoding

        with self.path.open("r", encoding=selected_encoding, errors=errors, newline="") as stream:

            def line_iterator() -> Iterator[str]:
                for line in stream:
                    self._track_text_bytes(line, selected_encoding)
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
        errors: str = "replace",
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
        errors: str = "replace",
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
        errors: str = "replace",
        fieldnames: list[str] | tuple[str, ...] | None = None,
        dialect: str = "excel",
        **csv_options: Any,
    ) -> Iterator[Iterator[dict[str, Any]]]:
        """Stream CSV rows as dictionaries."""
        selected_encoding = encoding or self.metadata.encoding_hint or _default_encoding()
        self.metadata.encoding_hint = selected_encoding
        with self.path.open("r", encoding=selected_encoding, errors=errors, newline="") as stream:
            reader = csv.DictReader(
                stream,
                fieldnames=fieldnames,
                dialect=dialect,
                **csv_options,
            )

            def row_iterator() -> Iterator[dict[str, Any]]:
                for row in reader:
                    self._track_text_bytes(_csv_row_size_hint(row), selected_encoding)
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
            compression_hint=self.metadata.compression_hint,
            base64_detected=self.metadata.base64_detected,
            decode_strategy=self.metadata.decode_strategy,
            bytes_read=self.metadata.bytes_read,
            warnings=list(self.metadata.warnings),
            errors=list(self.metadata.errors),
        )

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


def _csv_row_size_hint(row: dict[str, Any]) -> str:
    return ",".join("" if value is None else str(value) for value in row.values())
