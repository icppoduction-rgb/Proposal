"""EN: Core cursor-based log browsing helpers used by log-service.
RU: Основные cursor-based инструменты просмотра логов, используемые log-service.
"""

from __future__ import annotations

import base64
import binascii
import heapq
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

from cybersec_platform.db.session import get_settings
from cybersec_platform.observability import LogEntryOut, LogQueryOut, LogQueryParams, log_event, sanitize_log_payload

logger = logging.getLogger(__name__)


@dataclass(frozen=True, order=True)
class _EntryPosition:
    """EN: Stable cursor position used to continue scanning ordered log streams.
    RU: Стабильная позиция курсора для продолжения сканирования упорядоченных потоков логов.
    """

    timestamp: str
    service: str
    source_file: str
    line_number: int


@dataclass
class _ScoredEntry:
    """EN: Internal entry wrapper with precomputed ordering key.
    RU: Внутренняя обёртка записи с заранее вычисленным ключом сортировки.
    """

    position: _EntryPosition
    payload: LogEntryOut


@dataclass
class _HeapItem:
    """EN: Heap wrapper that keeps per-file iterators globally ordered.
    RU: Обёртка для heap, которая поддерживает глобальный порядок между per-file итераторами.
    """

    scored_entry: _ScoredEntry
    iterator: Iterator[_ScoredEntry]
    sort: str

    def __lt__(self, other: "_HeapItem") -> bool:
        if self.sort == "desc":
            return self.scored_entry.position > other.scored_entry.position
        return self.scored_entry.position < other.scored_entry.position


def list_available_log_services(logs_root: Path | None = None) -> list[str]:
    """EN: Return all service names that currently have a log directory.
    RU: Возвращает все имена сервисов, для которых сейчас существует директория логов.

    Args:
        logs_root: EN: Optional log root override for tests or embedded use. RU: Необязательное переопределение корня логов для тестов или встроенного использования.

    Returns:
        EN: Sorted service names.
        RU: Отсортированные имена сервисов.

    Side Effects:
        EN: Reads the filesystem only.
        RU: Только читает файловую систему.

    Raises:
        EN: Does not raise when the root directory is missing.
        RU: Не выбрасывает исключения, если корневая директория отсутствует.
    """

    root = logs_root or Path(get_settings().logs_path)
    if not root.exists():
        return []
    services = sorted(item.name for item in root.iterdir() if item.is_dir())
    log_event(logger, logging.INFO, "Resolved log service catalog", function="list_available_log_services", service_count=len(services))
    return services


def query_logs(params: LogQueryParams, logs_root: Path | None = None) -> LogQueryOut:
    """EN: Stream matching log entries and build one cursor page.
    RU: Потоково читает подходящие записи логов и формирует одну cursor-страницу.

    Args:
        params: EN: Filter and pagination parameters. RU: Параметры фильтрации и пагинации.
        logs_root: EN: Optional log root override for tests. RU: Необязательное переопределение корня логов для тестов.

    Returns:
        EN: Cursor-based page of log records.
        RU: Cursor-based страница лог-записей.

    Side Effects:
        EN: Reads matching log files from disk.
        RU: Читает подходящие лог-файлы с диска.

    Raises:
        EN: OSError when log files cannot be read.
        RU: OSError, если лог-файлы не удалось прочитать.
    """

    root = logs_root or Path(get_settings().logs_path)
    available_services = list_available_log_services(root)
    target_services = params.services or available_services
    cursor_position = _decode_cursor(params.cursor)
    heap: list[_HeapItem] = []

    for file_path in _iter_log_files(root, target_services, params.date_from, params.date_to, params.sort):
        iterator = _iter_matching_entries(file_path, params, reverse=params.sort == "desc")
        first_entry = _advance_after_cursor(iterator, cursor_position, params.sort)
        if first_entry is not None:
            heapq.heappush(heap, _HeapItem(scored_entry=first_entry, iterator=iterator, sort=params.sort))

    visible_entries: list[_ScoredEntry] = []
    while heap and len(visible_entries) < params.limit + 1:
        heap_item = heapq.heappop(heap)
        visible_entries.append(heap_item.scored_entry)
        next_entry = next(heap_item.iterator, None)
        if next_entry is not None:
            heapq.heappush(heap, _HeapItem(scored_entry=next_entry, iterator=heap_item.iterator, sort=params.sort))

    has_more = len(visible_entries) > params.limit
    visible_entries = visible_entries[: params.limit]
    next_cursor = _encode_cursor(visible_entries[-1].position) if has_more and visible_entries else None
    invalid_rows = sum(1 for item in visible_entries if not item.payload.is_valid_json)
    result = LogQueryOut(
        items=[item.payload for item in visible_entries],
        next_cursor=next_cursor,
        has_more=has_more,
        invalid_rows_in_page=invalid_rows,
        available_services=available_services,
    )
    log_event(
        logger,
        logging.INFO,
        "Built log cursor page",
        function="query_logs",
        item_count=len(result.items),
        has_more=result.has_more,
        invalid_rows_in_page=result.invalid_rows_in_page,
        services=target_services,
        sort=params.sort,
    )
    return result


def _iter_log_files(
    root: Path,
    services: list[str],
    date_from: date | None,
    date_to: date | None,
    sort: str,
) -> Iterator[Path]:
    """EN: Yield candidate log files ordered by partition date and service name.
    RU: Возвращает кандидатные лог-файлы, упорядоченные по дате партиции и имени сервиса.
    """

    file_paths: list[Path] = []
    for service in services:
        service_dir = root / service
        if not service_dir.exists():
            continue
        for file_path in service_dir.glob(f"{service}-*.json.log"):
            file_date = _parse_file_date(file_path)
            if date_from and file_date and file_date < date_from:
                continue
            if date_to and file_date and file_date > date_to:
                continue
            file_paths.append(file_path)
    file_paths.sort(key=lambda path: (_parse_file_date(path) or date.min, path.parent.name, path.name), reverse=sort == "desc")
    yield from file_paths


def _iter_matching_entries(file_path: Path, params: LogQueryParams, *, reverse: bool) -> Iterator[_ScoredEntry]:
    """EN: Yield matching entries from a single JSONL file.
    RU: Возвращает подходящие записи из одного JSONL-файла.
    """

    service = file_path.parent.name
    scored_entries: list[_ScoredEntry] = []
    with file_path.open("r", encoding="utf-8") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
                if not isinstance(payload, dict):
                    raise ValueError("Log entry must be a JSON object")
                entry = _build_valid_entry(service, file_path, line_number, payload)
            except (json.JSONDecodeError, ValueError) as exc:
                entry = _build_invalid_entry(service, file_path, line_number, stripped, str(exc))
            if _matches_filters(entry, params):
                position = _build_position(entry)
                scored_entries.append(_ScoredEntry(position=position, payload=entry))
    if reverse:
        scored_entries.reverse()
    yield from scored_entries


def _advance_after_cursor(iterator: Iterator[_ScoredEntry], cursor: _EntryPosition | None, sort: str) -> _ScoredEntry | None:
    """EN: Advance an iterator to the first entry visible after the current cursor.
    RU: Перемещает iterator к первой записи, видимой после текущего курсора.
    """

    for scored_entry in iterator:
        if _is_after_cursor(scored_entry.position, cursor, sort):
            return scored_entry
    return None


def _build_valid_entry(service: str, file_path: Path, line_number: int, payload: dict[str, Any]) -> LogEntryOut:
    """EN: Convert one valid JSON object into the API log entry shape.
    RU: Преобразует один корректный JSON-объект в форму лог-записи API.
    """

    sanitized = sanitize_log_payload(payload)
    timestamp = sanitized.get("timestamp")
    return LogEntryOut(
        id=f"{service}:{file_path.name}:{line_number}",
        timestamp=str(timestamp) if timestamp else None,
        service=str(sanitized.get("service") or service),
        level=str(sanitized.get("level") or "INFO"),
        function=str(sanitized.get("function") or "unknown"),
        message=str(sanitized.get("message") or ""),
        request=sanitized.get("request") if isinstance(sanitized.get("request"), dict) else {},
        error=sanitized.get("error"),
        context=sanitized.get("context") if isinstance(sanitized.get("context"), dict) else {},
        source_file=str(file_path),
        line_number=line_number,
        is_valid_json=True,
    )


def _build_invalid_entry(service: str, file_path: Path, line_number: int, raw_line: str, error_message: str) -> LogEntryOut:
    """EN: Convert an invalid JSON line into a synthetic warning entry.
    RU: Преобразует невалидную JSON-строку в синтетическую warning-запись.
    """

    return LogEntryOut(
        id=f"{service}:{file_path.name}:{line_number}",
        timestamp=None,
        service=service,
        level="WARNING",
        function="log_parser",
        message="Invalid JSONL record",
        request={},
        error={"type": "InvalidJsonLine", "message": error_message},
        context={},
        source_file=str(file_path),
        line_number=line_number,
        is_valid_json=False,
        raw_line=raw_line[:500],
    )


def _matches_filters(entry: LogEntryOut, params: LogQueryParams) -> bool:
    """EN: Apply query-level filters to a parsed log entry.
    RU: Применяет фильтры запроса к разобранной лог-записи.
    """

    if params.services and entry.service not in params.services:
        return False
    if params.level and entry.level.lower() != params.level.lower():
        return False
    if params.function and params.function.lower() not in entry.function.lower():
        return False
    if params.message and params.message.lower() not in entry.message.lower():
        return False
    error_blob = json.dumps(entry.error, ensure_ascii=False) if entry.error is not None else ""
    if params.error_text and params.error_text.lower() not in error_blob.lower():
        return False
    search_blob = " ".join([entry.service, entry.level, entry.function, entry.message, error_blob]).lower()
    if params.search and params.search.lower() not in search_blob:
        return False
    parsed_timestamp = _parse_timestamp(entry.timestamp)
    if params.date_from and parsed_timestamp and parsed_timestamp.date() < params.date_from:
        return False
    if params.date_to and parsed_timestamp and parsed_timestamp.date() > params.date_to:
        return False
    if params.time_from and parsed_timestamp and parsed_timestamp.time() < params.time_from:
        return False
    if params.time_to and parsed_timestamp and parsed_timestamp.time() > params.time_to:
        return False
    if (params.time_from or params.time_to) and parsed_timestamp is None:
        return False
    return True


def _build_position(entry: LogEntryOut) -> _EntryPosition:
    """EN: Build the stable ordering position used in cursor comparisons.
    RU: Формирует стабильную позицию сортировки, используемую в сравнениях курсора.
    """

    return _EntryPosition(
        timestamp=entry.timestamp or "",
        service=entry.service,
        source_file=entry.source_file,
        line_number=entry.line_number,
    )


def _encode_cursor(position: _EntryPosition) -> str:
    """EN: Serialize a cursor position into a URL-safe string.
    RU: Сериализует позицию курсора в URL-safe строку.
    """

    payload = {
        "timestamp": position.timestamp,
        "service": position.service,
        "source_file": position.source_file,
        "line_number": position.line_number,
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return encoded.decode("ascii")


def _decode_cursor(cursor: str | None) -> _EntryPosition | None:
    """EN: Parse a cursor string into an internal position object.
    RU: Разбирает строку курсора во внутренний объект позиции.
    """

    if not cursor:
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode("ascii") + b"==="))
    except (ValueError, binascii.Error, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return _EntryPosition(
            timestamp=str(payload.get("timestamp") or ""),
            service=str(payload["service"]),
            source_file=str(payload["source_file"]),
            line_number=int(payload["line_number"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _is_after_cursor(position: _EntryPosition, cursor: _EntryPosition | None, sort: str) -> bool:
    """EN: Check whether a position belongs after the cursor in the requested order.
    RU: Проверяет, находится ли позиция после курсора в запрошенном порядке сортировки.
    """

    if cursor is None:
        return True
    if sort == "desc":
        return position < cursor
    return position > cursor


def _parse_timestamp(value: str | None) -> datetime | None:
    """EN: Parse ISO-8601 timestamps used in structured logs.
    RU: Разбирает ISO-8601 timestamp, используемый в структурированных логах.
    """

    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _parse_file_date(file_path: Path) -> date | None:
    """EN: Extract the partition date from the JSONL filename.
    RU: Извлекает дату партиции из имени JSONL-файла.
    """

    stem = file_path.name.removesuffix(".json.log")
    _, _, date_part = stem.rpartition("-")
    try:
        return date.fromisoformat(date_part)
    except ValueError:
        return None
