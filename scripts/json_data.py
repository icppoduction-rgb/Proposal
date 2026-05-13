from __future__ import annotations

import json
from pathlib import Path
from typing import Any


JsonObject = dict[str, Any]
JsonPayload = JsonObject | list[JsonObject]


class JsonDataError(Exception):
    """Base exception for JSON data file errors."""


class UnsupportedJsonFormatError(JsonDataError):
    """Raised when a file extension is not supported."""


class InvalidJsonFileError(JsonDataError):
    """Raised when a file contains invalid JSON syntax."""


class InvalidJsonDataError(JsonDataError):
    """Raised when input or stored data has an unsupported type."""


class JsonFileIOError(JsonDataError):
    """Raised when a file cannot be read or written."""


class BaseFormatHandler:
    """Base handler for one JSON-family file format."""

    def read(self, path: Path, encoding: str) -> JsonPayload:
        """Reads data from a file and returns a validated payload."""
        raise NotImplementedError

    def write(
        self,
        path: Path,
        data: JsonPayload,
        encoding: str,
        *,
        ensure_ascii: bool,
        indent: int,
    ) -> None:
        """Writes a validated payload to a file."""
        raise NotImplementedError

    def update(
        self,
        path: Path,
        new_data: JsonPayload,
        encoding: str,
        *,
        ensure_ascii: bool,
        indent: int,
    ) -> JsonPayload:
        """Reads existing data, merges new data, writes the result and returns it."""
        current_data = self.read(path=path, encoding=encoding)
        updated_data = self.merge(current_data=current_data, new_data=new_data)
        self.write(
            path=path,
            data=updated_data,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            indent=indent,
        )
        return updated_data

    def merge(self, current_data: JsonPayload, new_data: JsonPayload) -> JsonPayload:
        """Merges new data into existing data using format-specific rules."""
        raise NotImplementedError

    def normalize_records(self, data: JsonPayload) -> list[JsonObject]:
        """Converts a dict or list of dicts into a list of records."""
        self.validate_payload(data)
        return [data] if isinstance(data, dict) else data

    def validate_payload(self, data: Any) -> None:
        """Validates that data is either a dict or a list of dicts."""
        if isinstance(data, dict):
            return

        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return

        raise InvalidJsonDataError("Data must be a dict or a list of dicts")

    def write_atomic(self, path: Path, content: str, encoding: str) -> None:
        """Writes content through a temporary file and atomically replaces target."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(f"{path.name}.tmp")

        try:
            with temp_path.open("w", encoding=encoding, newline="\n") as file:
                file.write(content)
            temp_path.replace(path)
        except OSError as error:
            if temp_path.exists():
                temp_path.unlink()
            raise JsonFileIOError(f"Cannot write file: {path}") from error

    def read_text(self, path: Path, encoding: str) -> str:
        """Reads file text and converts OS errors to domain errors."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise JsonFileIOError(f"Path is not a file: {path}")

        try:
            return path.read_text(encoding=encoding)
        except OSError as error:
            raise JsonFileIOError(f"Cannot read file: {path}") from error


class JsonFormatHandler(BaseFormatHandler):
    """Handler for regular .json files."""

    def read(self, path: Path, encoding: str) -> JsonPayload:
        """Reads a JSON object or a JSON array of objects."""
        content = self.read_text(path=path, encoding=encoding)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as error:
            raise InvalidJsonFileError(f"File contains invalid JSON: {path}") from error

        self.validate_payload(data)
        return data

    def write(
        self,
        path: Path,
        data: JsonPayload,
        encoding: str,
        *,
        ensure_ascii: bool,
        indent: int,
    ) -> None:
        """Writes a dict as JSON object or a list of dicts as JSON array."""
        self.validate_payload(data)
        content = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        self.write_atomic(path=path, content=f"{content}\n", encoding=encoding)

    def merge(self, current_data: JsonPayload, new_data: JsonPayload) -> JsonPayload:
        """Merges dicts by keys and appends records when either side is a list."""
        self.validate_payload(current_data)
        self.validate_payload(new_data)

        if isinstance(current_data, dict) and isinstance(new_data, dict):
            return current_data | new_data

        current_records = self.normalize_records(current_data)
        new_records = self.normalize_records(new_data)
        return current_records + new_records


class JsonLinesFormatHandler(BaseFormatHandler):
    """Handler for .jsonl and .ndjson files."""

    def read(self, path: Path, encoding: str) -> list[JsonObject]:
        """Reads JSON Lines or NDJSON and returns a list of dicts."""
        content = self.read_text(path=path, encoding=encoding)
        records: list[JsonObject] = []

        for line_number, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise InvalidJsonFileError(
                    f"File contains invalid JSON at line {line_number}: {path}"
                ) from error

            if not isinstance(record, dict):
                raise InvalidJsonDataError(
                    f"JSONL/NDJSON line {line_number} must contain a JSON object: {path}"
                )

            records.append(record)

        return records

    def write(
        self,
        path: Path,
        data: JsonPayload,
        encoding: str,
        *,
        ensure_ascii: bool,
        indent: int,
    ) -> None:
        """Writes one JSON object per line."""
        records = self.normalize_records(data)
        lines = [json.dumps(record, ensure_ascii=ensure_ascii) for record in records]
        content = "\n".join(lines)
        if content:
            content = f"{content}\n"
        self.write_atomic(path=path, content=content, encoding=encoding)

    def merge(self, current_data: JsonPayload, new_data: JsonPayload) -> list[JsonObject]:
        """Appends new records to existing JSON Lines records."""
        current_records = self.normalize_records(current_data)
        new_records = self.normalize_records(new_data)
        return current_records + new_records


class JsonData:
    """Universal interface for .json, .jsonl and .ndjson files."""

    _handlers: dict[str, BaseFormatHandler] = {
        ".json": JsonFormatHandler(),
        ".jsonl": JsonLinesFormatHandler(),
        ".ndjson": JsonLinesFormatHandler(),
    }

    def __init__(self, file_path: str | Path | None = None, encoding: str = "utf-8") -> None:
        """Stores an optional default file path and text encoding."""
        self.file_path = Path(file_path) if file_path is not None else None
        self.encoding = encoding

    @classmethod
    def read_file(
        cls,
        file_path: str | Path,
        *,
        default: Any = None,
        encoding: str = "utf-8",
    ) -> Any:
        """Reads data from a provided path using a handler selected by extension."""
        return cls(file_path=file_path, encoding=encoding).read(default=default)

    @classmethod
    def write_file(
        cls,
        file_path: str | Path,
        data: JsonPayload,
        *,
        indent: int = 4,
        ensure_ascii: bool = False,
        encoding: str = "utf-8",
    ) -> None:
        """Writes data to a provided path using a handler selected by extension."""
        cls(file_path=file_path, encoding=encoding).write(
            data=data,
            indent=indent,
            ensure_ascii=ensure_ascii,
        )

    @classmethod
    def update_file(
        cls,
        file_path: str | Path,
        data: JsonPayload,
        *,
        indent: int = 4,
        ensure_ascii: bool = False,
        encoding: str = "utf-8",
    ) -> JsonPayload:
        """Updates a provided path using a handler selected by extension."""
        return cls(file_path=file_path, encoding=encoding).update(
            new_data=data,
            indent=indent,
            ensure_ascii=ensure_ascii,
        )

    @classmethod
    def register_handler(cls, extension: str, handler: BaseFormatHandler) -> None:
        """Registers a new format handler or replaces an existing handler."""
        normalized_extension = cls._normalize_extension(extension)
        cls._handlers[normalized_extension] = handler

    def read(self, default: Any = None) -> Any:
        """Reads data from the configured file path."""
        path = self._require_file_path()

        if not path.exists() or path.stat().st_size == 0:
            if default is not None:
                return default
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

        return self._get_handler(path).read(path=path, encoding=self.encoding)

    def write(self, data: JsonPayload, indent: int = 4, ensure_ascii: bool = False) -> None:
        """Writes data to the configured file path."""
        path = self._require_file_path()
        self._get_handler(path).write(
            path=path,
            data=data,
            encoding=self.encoding,
            ensure_ascii=ensure_ascii,
            indent=indent,
        )

    def write_jsonl(self, records: JsonPayload, ensure_ascii: bool = False) -> int:
        """Writes records as JSON Lines and returns the number of written records."""
        path = self._require_file_path()
        handler = JsonLinesFormatHandler()
        normalized_records = handler.normalize_records(records)
        handler.write(
            path=path,
            data=normalized_records,
            encoding=self.encoding,
            ensure_ascii=ensure_ascii,
            indent=0,
        )
        return len(normalized_records)

    def update(
        self,
        new_data: JsonPayload,
        indent: int = 4,
        ensure_ascii: bool = False,
    ) -> JsonPayload:
        """Reads, merges and writes data to the configured file path."""
        path = self._require_file_path()
        return self._get_handler(path).update(
            path=path,
            new_data=new_data,
            encoding=self.encoding,
            ensure_ascii=ensure_ascii,
            indent=indent,
        )

    def delete(self) -> None:
        """Deletes the configured file if it exists."""
        path = self._require_file_path()

        try:
            if path.exists():
                path.unlink()
        except OSError as error:
            raise JsonFileIOError(f"Cannot delete file: {path}") from error

    def exists(self) -> bool:
        """Checks whether the configured file exists."""
        return self._require_file_path().exists()

    def _require_file_path(self) -> Path:
        """Returns configured path or raises an explicit configuration error."""
        if self.file_path is None:
            raise ValueError("file_path is required")
        return self.file_path

    def _get_handler(self, path: Path) -> BaseFormatHandler:
        """Returns a format handler by file extension."""
        extension = path.suffix.lower()
        handler = self._handlers.get(extension)

        if handler is None:
            raise UnsupportedJsonFormatError(f"Unsupported file format '{extension or '<none>'}': {path}")

        return handler

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        """Normalizes extension values before registration."""
        value = extension.strip().lower()
        return value if value.startswith(".") else f".{value}"
