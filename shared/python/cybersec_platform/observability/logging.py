"""EN: Centralized JSONL logging and request context propagation helpers.
RU: Централизованное JSONL-логирование и инструменты передачи контекста запроса.
"""

from __future__ import annotations

import inspect
import json
import logging
import threading
import traceback
from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")

_REQUEST_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})

_SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "cookie",
    "password",
    "refresh_token",
    "secret",
    "token",
}

_STANDARD_LOG_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


def sanitize_log_payload(value: Any) -> Any:
    """EN: Recursively redact sensitive values before persistence or display.
    RU: Рекурсивно маскирует чувствительные значения перед сохранением и отображением.

    Args:
        value: EN: Arbitrary payload to sanitize. RU: Произвольная структура для маскировки.

    Returns:
        EN: Sanitized payload safe for logs and UI.
        RU: Очищенная структура, безопасная для логов и UI.

    Side Effects:
        EN: None.
        RU: Отсутствуют.

    Raises:
        EN: Does not raise by design.
        RU: По замыслу не выбрасывает исключения.
    """

    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key in _SENSITIVE_KEYS:
                sanitized[str(key)] = "***REDACTED***"
            else:
                sanitized[str(key)] = sanitize_log_payload(item)
        return sanitized
    if isinstance(value, (list, tuple, set)):
        return [sanitize_log_payload(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def get_request_context() -> dict[str, Any]:
    """EN: Return the current request or task context bound to the active execution.
    RU: Возвращает текущий контекст запроса или задачи, привязанный к активному выполнению.

    Args:
        None.

    Returns:
        EN: A shallow copy of the current context dictionary.
        RU: Поверхностная копия текущего словаря контекста.

    Side Effects:
        EN: None.
        RU: Отсутствуют.

    Raises:
        EN: Does not raise by design.
        RU: По замыслу не выбрасывает исключения.
    """

    return dict(_REQUEST_CONTEXT.get())


def set_request_context(payload: Mapping[str, Any] | None = None, **updates: Any) -> Token:
    """EN: Replace the active request context with a sanitized mapping.
    RU: Полностью заменяет активный контекст запроса очищенным словарём.

    Args:
        payload: EN: Base context mapping. RU: Базовый словарь контекста.
        updates: EN: Extra context fields merged into the payload. RU: Дополнительные поля, объединяемые с базовым словарём.

    Returns:
        EN: Context token for later reset.
        RU: Токен контекста для последующего сброса.

    Side Effects:
        EN: Updates the process-local context variable.
        RU: Обновляет process-local context variable.

    Raises:
        EN: Does not raise by design.
        RU: По замыслу не выбрасывает исключения.
    """

    next_payload = dict(payload or {})
    next_payload.update(updates)
    return _REQUEST_CONTEXT.set(sanitize_log_payload(next_payload))


@contextmanager
def request_context(payload: Mapping[str, Any] | None = None, **updates: Any) -> Iterator[dict[str, Any]]:
    """EN: Temporarily bind request or task metadata to nested log records.
    RU: Временно привязывает метаданные запроса или задачи к вложенным лог-записям.

    Args:
        payload: EN: Base context payload. RU: Базовый словарь контекста.
        updates: EN: Extra context fields. RU: Дополнительные поля контекста.

    Returns:
        EN: The sanitized context available inside the block.
        RU: Очищенный контекст, доступный внутри блока.

    Side Effects:
        EN: Temporarily mutates the current context variable.
        RU: Временно изменяет текущую context variable.

    Raises:
        EN: Propagates exceptions from the managed block unchanged.
        RU: Пробрасывает исключения из управляемого блока без изменений.
    """

    token = set_request_context(payload, **updates)
    try:
        yield get_request_context()
    finally:
        _REQUEST_CONTEXT.reset(token)


class JsonFileHandler(logging.Handler):
    """EN: Append-only JSONL handler with per-day file partitioning by service name.
    RU: Append-only JSONL handler с разбиением файлов по сервису и дате.
    """

    def __init__(self, service_name: str, logs_root: Path) -> None:
        """EN: Initialize handler storage and lock.
        RU: Инициализирует путь хранения и lock.

        Args:
            service_name: EN: Logical service identifier used in file names. RU: Логическое имя сервиса для имён файлов.
            logs_root: EN: Root directory for structured logs. RU: Корневая директория для структурированных логов.

        Returns:
            EN: None.
            RU: None.

        Side Effects:
            EN: Creates service-specific log directory.
            RU: Создаёт директорию логов сервиса.

        Raises:
            EN: OSError if the directory cannot be created.
            RU: OSError, если директорию не удалось создать.
        """

        super().__init__()
        self.service_name = service_name
        self.logs_root = logs_root
        self._lock = threading.Lock()
        (self.logs_root / self.service_name).mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:
        """EN: Persist a single log record as a JSONL entry.
        RU: Сохраняет одну лог-запись как JSONL-строку.

        Args:
            record: EN: Python log record to serialize. RU: Python log record для сериализации.

        Returns:
            EN: None.
            RU: None.

        Side Effects:
            EN: Appends one line to the daily JSON log file.
            RU: Добавляет одну строку в ежедневный JSON-файл логов.

        Raises:
            EN: Never raises to the caller; internal failures use handleError.
            RU: Не выбрасывает исключения наружу; внутренние ошибки обрабатываются через handleError.
        """

        try:
            entry = self._build_entry(record)
            target = self._resolve_target_path()
            with self._lock:
                with target.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            self.handleError(record)

    def _resolve_target_path(self) -> Path:
        """EN: Build the append target for the current local date.
        RU: Формирует путь назначения для текущей локальной даты.

        Args:
            None.

        Returns:
            EN: Daily JSONL file path.
            RU: Путь к ежедневному JSONL-файлу.

        Side Effects:
            EN: Ensures parent directory exists.
            RU: Гарантирует наличие родительской директории.

        Raises:
            EN: OSError if the directory cannot be created.
            RU: OSError, если директорию не удалось создать.
        """

        service_dir = self.logs_root / self.service_name
        service_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{self.service_name}-{datetime.now().date().isoformat()}.json.log"
        return service_dir / file_name

    def _build_entry(self, record: logging.LogRecord) -> dict[str, Any]:
        """EN: Convert a Python log record into the platform JSON schema.
        RU: Преобразует Python log record в платформенную JSON-схему.

        Args:
            record: EN: Source logging record. RU: Исходная logging-запись.

        Returns:
            EN: JSON-serializable dictionary matching the required fields.
            RU: JSON-сериализуемый словарь с обязательными полями.

        Side Effects:
            EN: None.
            RU: Отсутствуют.

        Raises:
            EN: Does not raise by design when called correctly.
            RU: При корректном использовании исключений не выбрасывает.
        """

        extra_payload = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_RECORD_KEYS and not key.startswith("_")
        }
        request_payload = extra_payload.pop("request", None)
        function_name = str(extra_payload.pop("function", record.funcName or record.name))
        explicit_error = extra_payload.pop("error", None)
        error_payload = self._build_error_payload(record, explicit_error)
        message = record.getMessage()
        context = sanitize_log_payload(extra_payload)
        return {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "function": function_name,
            "request": sanitize_log_payload(request_payload if request_payload is not None else get_request_context()),
            "message": message,
            "error": error_payload,
            "context": context,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }

    def _build_error_payload(self, record: logging.LogRecord, explicit_error: Any) -> Any:
        """EN: Convert an exception or explicit error into JSON-friendly form.
        RU: Преобразует исключение или явную ошибку в JSON-совместимую форму.

        Args:
            record: EN: Source logging record. RU: Исходная лог-запись.
            explicit_error: EN: Explicit error payload supplied via extra fields. RU: Явный payload ошибки из extra-полей.

        Returns:
            EN: Structured error payload or None.
            RU: Структурированный payload ошибки либо None.

        Side Effects:
            EN: None.
            RU: Отсутствуют.

        Raises:
            EN: Does not raise by design.
            RU: По замыслу не выбрасывает исключения.
        """

        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            return sanitize_log_payload(
                {
                    "type": exc_type.__name__ if exc_type else "Exception",
                    "message": str(exc_value),
                    "stack_trace": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                }
            )
        if explicit_error is None:
            return None
        return sanitize_log_payload(explicit_error)


def configure_logging(service_name: str, *, level: int = logging.INFO) -> logging.Logger:
    """EN: Configure the root logger to write structured JSONL records for a service.
    RU: Настраивает root logger на запись структурированных JSONL-логов сервиса.

    Args:
        service_name: EN: Logical service identifier for routing logs. RU: Логическое имя сервиса для маршрутизации логов.
        level: EN: Logging severity threshold. RU: Порог уровня логирования.

    Returns:
        EN: Service logger instance ready for use.
        RU: Экземпляр логгера сервиса, готовый к использованию.

    Side Effects:
        EN: Replaces root logger handlers in the current process.
        RU: Заменяет handlers root logger в текущем процессе.

    Raises:
        EN: OSError if the log directory cannot be prepared.
        RU: OSError, если не удалось подготовить директорию логов.
    """

    from cybersec_platform.db.session import get_settings

    settings = get_settings()
    logs_root = Path(settings.logs_path)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(JsonFileHandler(service_name=service_name, logs_root=logs_root))
    root_logger.propagate = False
    service_logger = logging.getLogger(service_name)
    service_logger.setLevel(level)
    service_logger.info(
        "Structured logging configured",
        extra={"function": "configure_logging", "request": {"type": "service", "service": service_name}},
    )
    return service_logger


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    *,
    function: str,
    request: Mapping[str, Any] | None = None,
    error: Any = None,
    **context: Any,
) -> None:
    """EN: Emit a structured business-event record through the configured logger.
    RU: Отправляет структурированную запись бизнес-события через настроенный логгер.

    Args:
        logger: EN: Target logger instance. RU: Целевой экземпляр логгера.
        level: EN: Severity level. RU: Уровень серьёзности.
        message: EN: Human-readable event message. RU: Человекочитаемое сообщение события.
        function: EN: Logical function or operation name. RU: Логическое имя функции или операции.
        request: EN: Optional explicit request/task context. RU: Необязательный явный контекст запроса/задачи.
        error: EN: Optional error payload. RU: Необязательный payload ошибки.
        context: EN: Additional structured context fields. RU: Дополнительные структурированные поля контекста.

    Returns:
        EN: None.
        RU: None.

    Side Effects:
        EN: Persists a JSONL log record.
        RU: Сохраняет JSONL-лог-запись.

    Raises:
        EN: Propagates logger errors only if logging infrastructure fails catastrophically.
        RU: Пробрасывает ошибки только при критическом сбое инфраструктуры логирования.
    """

    logger.log(level, message, extra={"function": function, "request": request, "error": error, **context})


def observed(event_name: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """EN: Decorate sync or async functions with start/success/failure structured logs.
    RU: Декорирует sync/async-функции структурированными логами start/success/failure.

    Args:
        event_name: EN: Optional logical event name overriding the function name. RU: Необязательное имя события, переопределяющее имя функции.

    Returns:
        EN: Decorator that wraps the target callable.
        RU: Декоратор, оборачивающий целевой callable.

    Side Effects:
        EN: Adds structured log records around function execution.
        RU: Добавляет структурированные лог-записи вокруг выполнения функции.

    Raises:
        EN: Re-raises exceptions from the wrapped function unchanged.
        RU: Повторно выбрасывает исключения из обёрнутой функции без изменений.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        logger = logging.getLogger(func.__module__)
        function_name = func.__qualname__
        operation_name = event_name or function_name

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                log_event(logger, logging.INFO, f"{operation_name} started", function=function_name)
                try:
                    result = await func(*args, **kwargs)
                except Exception as exc:
                    logger.exception(
                        f"{operation_name} failed",
                        extra={"function": function_name, "error": {"type": type(exc).__name__, "message": str(exc)}},
                    )
                    raise
                log_event(logger, logging.INFO, f"{operation_name} completed", function=function_name)
                return result

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            log_event(logger, logging.INFO, f"{operation_name} started", function=function_name)
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                logger.exception(
                    f"{operation_name} failed",
                    extra={"function": function_name, "error": {"type": type(exc).__name__, "message": str(exc)}},
                )
                raise
            log_event(logger, logging.INFO, f"{operation_name} completed", function=function_name)
            return result

        return sync_wrapper

    return decorator
