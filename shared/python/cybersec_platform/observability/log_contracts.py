"""EN: Shared contracts for cursor-based structured log browsing.
RU: Общие контракты для cursor-based просмотра структурированных логов.
"""

from __future__ import annotations

from datetime import date, time
from typing import Any, Literal

from pydantic import BaseModel, Field


class LogQueryParams(BaseModel):
    """EN: Filter and pagination parameters for log browsing APIs.
    RU: Параметры фильтрации и пагинации для API просмотра логов.

    Args:
        None.

    Returns:
        EN: Pydantic model instance with normalized filter values.
        RU: Экземпляр Pydantic-модели с нормализованными значениями фильтров.

    Side Effects:
        EN: Performs validation and type coercion.
        RU: Выполняет валидацию и преобразование типов.

    Raises:
        EN: ValidationError when incoming values do not match the schema.
        RU: ValidationError, если входные значения не соответствуют схеме.
    """

    services: list[str] = Field(default_factory=list)
    date_from: date | None = None
    date_to: date | None = None
    time_from: time | None = None
    time_to: time | None = None
    level: str | None = None
    function: str | None = None
    message: str | None = None
    error_text: str | None = None
    search: str | None = None
    sort: Literal["asc", "desc"] = "desc"
    cursor: str | None = None
    limit: int = Field(default=50, ge=1, le=200)


class LogEntryOut(BaseModel):
    """EN: Structured log record returned by log browsing APIs.
    RU: Структурированная лог-запись, возвращаемая API просмотра логов.

    Args:
        None.

    Returns:
        EN: Pydantic model instance describing a single log row.
        RU: Экземпляр Pydantic-модели, описывающий одну строку лога.

    Side Effects:
        EN: Performs validation and serialization support only.
        RU: Только выполняет валидацию и поддержку сериализации.

    Raises:
        EN: ValidationError when payload shape is invalid.
        RU: ValidationError, если структура payload некорректна.
    """

    id: str
    timestamp: str | None = None
    service: str
    level: str
    function: str
    message: str
    request: dict[str, Any] = Field(default_factory=dict)
    error: Any = None
    context: dict[str, Any] = Field(default_factory=dict)
    source_file: str
    line_number: int
    is_valid_json: bool = True
    raw_line: str | None = None


class LogQueryOut(BaseModel):
    """EN: Cursor-based response for structured log browsing.
    RU: Cursor-based ответ для просмотра структурированных логов.

    Args:
        None.

    Returns:
        EN: Pydantic model instance describing one cursor page.
        RU: Экземпляр Pydantic-модели, описывающий одну cursor-страницу.

    Side Effects:
        EN: Performs validation and serialization support only.
        RU: Только выполняет валидацию и поддержку сериализации.

    Raises:
        EN: ValidationError when payload shape is invalid.
        RU: ValidationError, если структура payload некорректна.
    """

    items: list[LogEntryOut] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    invalid_rows_in_page: int = 0
    available_services: list[str] = Field(default_factory=list)
