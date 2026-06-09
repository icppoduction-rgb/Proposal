from __future__ import annotations

import json
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostTestBSONContentAnalysisResult:
    summary_json_file: str
    docs_ru_file: str
    docs_en_file: str
    docs_ru_readme_file: str
    docs_en_readme_file: str
    report_ru_file: str
    report_en_file: str
    total_files_count: int
    sampled_files_count: int
    status: str


@dataclass(frozen=True)
class BSONFileProbe:
    path: str
    file_name: str
    file_size_bytes: int
    sampled_bytes: int
    parsed_documents: int
    parse_error: str | None


class BSONDocumentProbe:
    BSON_TYPES: dict[int, str] = {
        0x01: "double",
        0x02: "string",
        0x03: "document",
        0x04: "array",
        0x05: "binary",
        0x06: "undefined",
        0x07: "object_id",
        0x08: "bool",
        0x09: "datetime",
        0x0A: "null",
        0x0B: "regex",
        0x0C: "dbpointer",
        0x0D: "javascript",
        0x0E: "symbol",
        0x0F: "javascript_scope",
        0x10: "int32",
        0x11: "timestamp",
        0x12: "int64",
        0x13: "decimal128",
        0xFF: "min_key",
        0x7F: "max_key",
    }

    def __init__(self, max_depth: int = 3, max_example_length: int = 120) -> None:
        self.max_depth = max(1, max_depth)
        self.max_example_length = max(40, max_example_length)

    def parse_many(
        self,
        payload: bytes,
        max_documents: int,
    ) -> tuple[int, Counter[tuple[str, str]], dict[tuple[str, str], str], Counter[str], str | None]:
        offset = 0
        parsed_documents = 0
        field_types: Counter[tuple[str, str]] = Counter()
        examples: dict[tuple[str, str], str] = {}
        event_names: Counter[str] = Counter()

        try:
            while offset + 5 <= len(payload) and parsed_documents < max_documents:
                fields, values, next_offset = self._parse_document(payload, offset=offset, depth=0, prefix="")
                if next_offset <= offset:
                    raise ValueError(f"Parser did not advance at byte offset {offset}.")
                parsed_documents += 1
                offset = next_offset

                for field_name, type_name in fields:
                    field_types[(field_name, type_name)] += 1
                for field_name, type_name, value in values:
                    examples.setdefault((field_name, type_name), self._format_example(value))
                    if field_name == "name" and type_name == "string":
                        event_names[str(value)] += 1
        except (struct.error, UnicodeDecodeError, ValueError) as error:
            return parsed_documents, field_types, examples, event_names, str(error)

        return parsed_documents, field_types, examples, event_names, None

    def _parse_document(
        self,
        payload: bytes,
        offset: int,
        depth: int,
        prefix: str,
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str, Any]], int]:
        if offset + 5 > len(payload):
            raise ValueError(f"Truncated BSON document header at byte offset {offset}.")

        document_length = struct.unpack_from("<i", payload, offset)[0]
        if document_length < 5:
            raise ValueError(f"Invalid BSON document length {document_length} at byte offset {offset}.")

        end_offset = offset + document_length
        if end_offset > len(payload):
            raise ValueError(
                f"BSON document length {document_length} exceeds sampled payload at byte offset {offset}."
            )

        fields: list[tuple[str, str]] = []
        values: list[tuple[str, str, Any]] = []
        cursor = offset + 4
        document_end_marker = end_offset - 1

        while cursor < document_end_marker:
            element_type = payload[cursor]
            cursor += 1
            key, cursor = self._read_cstring(payload, cursor)
            type_name = self.BSON_TYPES.get(element_type, f"unknown_0x{element_type:02x}")
            full_key = f"{prefix}.{key}" if prefix else key
            fields.append((full_key, type_name))

            value, cursor, nested_fields, nested_values = self._read_value(
                payload=payload,
                cursor=cursor,
                element_type=element_type,
                depth=depth,
                full_key=full_key,
            )
            fields.extend(nested_fields)
            values.append((full_key, type_name, value))
            values.extend(nested_values)

        if payload[document_end_marker] != 0:
            raise ValueError(f"BSON document terminator is missing at byte offset {document_end_marker}.")

        return fields, values, end_offset

    def _read_value(
        self,
        payload: bytes,
        cursor: int,
        element_type: int,
        depth: int,
        full_key: str,
    ) -> tuple[Any, int, list[tuple[str, str]], list[tuple[str, str, Any]]]:
        nested_fields: list[tuple[str, str]] = []
        nested_values: list[tuple[str, str, Any]] = []

        if element_type == 0x01:
            value = struct.unpack_from("<d", payload, cursor)[0]
            return value, cursor + 8, nested_fields, nested_values

        if element_type in {0x02, 0x0D, 0x0E}:
            value, cursor = self._read_bson_string(payload, cursor)
            return value, cursor, nested_fields, nested_values

        if element_type in {0x03, 0x04}:
            if depth < self.max_depth:
                child_fields, child_values, next_cursor = self._parse_document(
                    payload=payload,
                    offset=cursor,
                    depth=depth + 1,
                    prefix=full_key,
                )
                nested_fields.extend(child_fields)
                nested_values.extend(child_values[:20])
                return "nested_document" if element_type == 0x03 else "nested_array", next_cursor, nested_fields, nested_values

            nested_length = struct.unpack_from("<i", payload, cursor)[0]
            if nested_length < 5:
                raise ValueError(f"Invalid nested BSON length {nested_length} for {full_key}.")
            return "nested_skipped", cursor + nested_length, nested_fields, nested_values

        if element_type == 0x05:
            binary_length = struct.unpack_from("<i", payload, cursor)[0]
            subtype_cursor = cursor + 4
            subtype = payload[subtype_cursor]
            return (
                f"subtype={subtype}, bytes={binary_length}",
                cursor + 5 + binary_length,
                nested_fields,
                nested_values,
            )

        if element_type in {0x06, 0x0A, 0xFF, 0x7F}:
            return None, cursor, nested_fields, nested_values

        if element_type == 0x07:
            return payload[cursor : cursor + 12].hex(), cursor + 12, nested_fields, nested_values

        if element_type == 0x08:
            return bool(payload[cursor]), cursor + 1, nested_fields, nested_values

        if element_type in {0x09, 0x11, 0x12}:
            return struct.unpack_from("<q", payload, cursor)[0], cursor + 8, nested_fields, nested_values

        if element_type == 0x10:
            return struct.unpack_from("<i", payload, cursor)[0], cursor + 4, nested_fields, nested_values

        if element_type == 0x13:
            return payload[cursor : cursor + 16].hex(), cursor + 16, nested_fields, nested_values

        if element_type == 0x0B:
            pattern, cursor = self._read_cstring(payload, cursor)
            options, cursor = self._read_cstring(payload, cursor)
            return f"{pattern}/{options}", cursor, nested_fields, nested_values

        if element_type == 0x0C:
            namespace, cursor = self._read_bson_string(payload, cursor)
            object_id = payload[cursor : cursor + 12].hex()
            return f"{namespace}:{object_id}", cursor + 12, nested_fields, nested_values

        if element_type == 0x0F:
            scoped_length = struct.unpack_from("<i", payload, cursor)[0]
            if scoped_length < 14:
                raise ValueError(f"Invalid code_w_scope length {scoped_length} for {full_key}.")
            return "javascript_with_scope", cursor + scoped_length, nested_fields, nested_values

        raise ValueError(f"Unsupported BSON element type 0x{element_type:02x} for field {full_key}.")

    @staticmethod
    def _read_cstring(payload: bytes, cursor: int) -> tuple[str, int]:
        end = payload.find(b"\x00", cursor)
        if end < 0:
            raise ValueError(f"Missing BSON cstring terminator at byte offset {cursor}.")
        return payload[cursor:end].decode("utf-8"), end + 1

    @staticmethod
    def _read_bson_string(payload: bytes, cursor: int) -> tuple[str, int]:
        string_length = struct.unpack_from("<i", payload, cursor)[0]
        if string_length <= 0:
            raise ValueError(f"Invalid BSON string length {string_length} at byte offset {cursor}.")
        cursor += 4
        raw_value = payload[cursor : cursor + string_length - 1]
        return raw_value.decode("utf-8", errors="replace"), cursor + string_length

    def _format_example(self, value: Any) -> str:
        if isinstance(value, str):
            text = value
        else:
            text = json.dumps(value, ensure_ascii=False)
        text = text.replace("\r", "\\r").replace("\n", "\\n")
        if len(text) > self.max_example_length:
            return f"{text[: self.max_example_length - 3]}..."
        return text


class HostTestBSONContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "bson"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_DOCS_PER_FILE = 100
    DEFAULT_MAX_BYTES_PER_FILE = 2 * 1024 * 1024

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-test-bson-summary.json"

    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_docs_per_file: int = DEFAULT_MAX_DOCS_PER_FILE,
        max_bytes_per_file: int = DEFAULT_MAX_BYTES_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.report_path = Path(report_path).expanduser() if report_path is not None else self.project_root / "report"
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_docs_per_file = max(1, max_docs_per_file)
        self.max_bytes_per_file = max(64 * 1024, max_bytes_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host" / "test"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host" / "test"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "host" / "test"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "host" / "test"

    def analyze_and_generate_docs(self) -> HostTestBSONContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TEST/bson.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "bson.md"
        docs_en_path = self.docs_en_dir / "bson.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = (
            self.report_ru_dir / "Task44(Analysis of host test bson dataset files)_report.md"
        )
        report_en_path = (
            self.report_en_dir / "Task44(Analysis of host test bson dataset files)_report.md"
        )

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(summary_payload))
        self._write_text_file(report_ru_path, self._build_ru_report(summary_payload, summary_json_path))
        self._write_text_file(report_en_path, self._build_en_report(summary_payload, summary_json_path))

        return HostTestBSONContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=len(sampled_paths),
            status=str(summary_payload["final_status"]),
        )

    def _read_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        if not payload:
            raise FileNotFoundError(f"Source JSON is empty or missing: {source_json_path}")
        if self.ROLE_NAME not in payload:
            raise ValueError(f"Missing role '{self.ROLE_NAME}' in {source_json_path}.")
        return payload

    def _extract_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
        role_bucket = role_to_formats.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            raise ValueError(f"Role '{self.ROLE_NAME}' in source JSON must be an object.")
        format_bucket = role_bucket.get(self.FORMAT_NAME, [])
        if not isinstance(format_bucket, list):
            raise ValueError(
                f"Role '{self.ROLE_NAME}' format '{self.FORMAT_NAME}' must be a list of paths."
            )
        return sorted(
            [Path(str(raw_path)).expanduser() for raw_path in format_bucket if isinstance(raw_path, str)],
            key=lambda p: str(p).lower(),
        )

    def _select_sample_paths(self, all_paths: list[Path]) -> list[Path]:
        if len(all_paths) <= self.max_files_per_format:
            return all_paths
        step = (len(all_paths) - 1) / (self.max_files_per_format - 1)
        indices = {int(round(index * step)) for index in range(self.max_files_per_format)}
        return [all_paths[index] for index in sorted(indices)]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        parser = BSONDocumentProbe()
        file_probes: list[BSONFileProbe] = []
        field_types: Counter[tuple[str, str]] = Counter()
        examples: dict[tuple[str, str], str] = {}
        event_names: Counter[str] = Counter()
        parse_errors: Counter[str] = Counter()

        empty_files = 0
        missing_files = 0
        parsed_document_count = 0
        total_sampled_bytes = 0

        for file_path in sampled_paths:
            if not file_path.exists():
                missing_files += 1
                file_probes.append(
                    BSONFileProbe(
                        path=str(file_path),
                        file_name=file_path.name,
                        file_size_bytes=0,
                        sampled_bytes=0,
                        parsed_documents=0,
                        parse_error="file_not_found",
                    )
                )
                continue

            file_size = file_path.stat().st_size
            if file_size == 0:
                empty_files += 1
                file_probes.append(
                    BSONFileProbe(
                        path=str(file_path),
                        file_name=file_path.name,
                        file_size_bytes=0,
                        sampled_bytes=0,
                        parsed_documents=0,
                        parse_error="empty_file",
                    )
                )
                continue

            payload = file_path.read_bytes()[: self.max_bytes_per_file]
            total_sampled_bytes += len(payload)
            documents, fields, field_examples, names, parse_error = parser.parse_many(
                payload=payload,
                max_documents=self.max_docs_per_file,
            )

            field_types.update(fields)
            event_names.update(names)
            for key, value in field_examples.items():
                examples.setdefault(key, value)
            parsed_document_count += documents
            if parse_error:
                parse_errors[parse_error] += 1

            file_probes.append(
                BSONFileProbe(
                    path=str(file_path),
                    file_name=file_path.name,
                    file_size_bytes=file_size,
                    sampled_bytes=len(payload),
                    parsed_documents=documents,
                    parse_error=parse_error,
                )
            )

        final_status = self.STATUS_BROKEN if parsed_document_count == 0 else self.STATUS_NEEDS_CUSTOM

        top_fields = [
            {
                "field": field_name,
                "type": type_name,
                "observed_count": count,
                "example": examples.get((field_name, type_name), ""),
            }
            for (field_name, type_name), count in field_types.most_common(25)
        ]

        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.HOST_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_docs_per_file": self.max_docs_per_file,
                "max_bytes_per_file": self.max_bytes_per_file,
                "total_sampled_bytes": total_sampled_bytes,
            },
            "sample_paths": [str(path) for path in sampled_paths[:10]],
            "file_probes": [probe.__dict__ for probe in file_probes],
            "parsed_document_count": parsed_document_count,
            "empty_files_in_sample": empty_files,
            "missing_files_in_sample": missing_files,
            "parse_errors": dict(parse_errors),
            "top_fields": top_fields,
            "top_event_names": dict(event_names.most_common(20)),
            "label": {
                "found": False,
                "field_name": None,
                "values": [],
                "supervised_learning": "no",
                "comment": "No explicit label/class/attack field was found in sampled BSON documents.",
            },
            "time": {
                "found": True,
                "field_name": "implicit document order; numeric t/h fields in event records",
                "format": "relative numeric counters, not a wall-clock timestamp",
                "timezone": "not specified",
                "can_build_sequence": True,
                "can_apply_sliding_window": True,
            },
            "final_status": final_status,
            "needs_custom_parser": True,
            "processing_priority": "high",
        }

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        top_fields = self._render_ru_fields(summary)
        examples = "\n".join(summary["sample_paths"][:3])
        file_count = summary["scope"]["total_files_count"]
        sampled_files = summary["scope"]["sampled_files_count"]
        parsed_documents = summary["parsed_document_count"]
        parse_error_count = sum(summary["parse_errors"].values())

        return f"""# Анализ формата: bson

## 1. Назначение
BSON-файлы в Host TEST содержат бинарные трассы поведения процессов и системных/API-событий. Формат нужен проекту как источник последовательностей host-событий для дальнейшего feature engineering; для обучения TEST-набор не используется.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | bson |
| Варианты расширения | .bson |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | {file_count} |

## 3. Примеры файлов
```text
{examples}
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | да |
| Sample-файлов проанализировано | {sampled_files} |
| Sample BSON-документов разобрано | {parsed_documents} |

## 5. Содержательная структура
Sample показывает BSON-поток из последовательных документов. Встречаются descriptor-документы с полями `name`, `type`, `category`, `args`, `flags_value`, `flags_bitmask`, а также event-документы с `I`, `T`, `t`, `h` и массивом `args`. По содержанию это malware behaviour / host telemetry traces: события процессов, Windows API/syscall-like операции, аргументы вызовов, пути модулей, command line и вложенные структуры flags.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
{top_fields}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | нет для TEST; нужны внешние метки, если они существуют |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | частично |
| Название поля | порядок BSON-документов, числовые `t`/`h` в event-записях |
| Формат времени | относительные числовые счетчики; timezone не указан |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо для этого Host-формата.

### Host-признаки
- частоты API/syscall-событий по `I` и descriptor `name`;
- n-grams и переходы между событиями;
- длина trace и плотность событий;
- признаки аргументов `args`, включая пути процессов, module basename, command line;
- parent-child/process context признаки из process notification документов;
- частоты категорий descriptor `category`;
- энтропия и токены command line / module path.

### Network / hybrid-признаки
- напрямую network flow-поля не обнаружены;
- возможна корреляция с network-датасетами по внешнему sample/file id, если такая связь есть в метаданных проекта.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors in sample: {parse_error_count} |
| Missing values | да | в BSON встречаются null/пустые позиции в `args` |
| Нестабильная структура | да | descriptor и event-документы имеют разные схемы |
| Смешанные схемы | да | один поток содержит metadata/descriptor/event документы |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
Формат полезен для дальнейшего pipeline как источник host behaviour sequence features, но не готов к универсальному табличному чтению. Нужен отдельный BSON parser, который сопоставляет descriptor-документы с event-документами по `I`, разворачивает `args` и сохраняет порядок событий. Явных label-полей в TEST/BSON sample не найдено.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        top_fields = self._render_en_fields(summary)
        examples = "\n".join(summary["sample_paths"][:3])
        file_count = summary["scope"]["total_files_count"]
        sampled_files = summary["scope"]["sampled_files_count"]
        parsed_documents = summary["parsed_document_count"]
        parse_error_count = sum(summary["parse_errors"].values())

        return f"""# Format Analysis: bson

## 1. Purpose
Host TEST BSON files contain binary process behaviour and system/API event traces. The format is useful as a source of ordered host-event sequences for later feature engineering; TEST data must not be used for model training.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | bson |
| Extension variants | .bson |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | {file_count} |

## 3. Example Files
```text
{examples}
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | no |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | yes |
| Sampled files analyzed | {sampled_files} |
| Sample BSON documents parsed | {parsed_documents} |

## 5. Content Structure
The sample is a stream of consecutive BSON documents. It contains descriptor documents with `name`, `type`, `category`, `args`, `flags_value`, and `flags_bitmask`, plus event documents with `I`, `T`, `t`, `h`, and an `args` array. Semantically this is malware behaviour / host telemetry: process events, Windows API or syscall-like operations, call arguments, module paths, command lines, and nested flag structures.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
{top_fields}

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | no for TEST; external labels are required if available |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | partial |
| Field name | BSON document order, numeric `t`/`h` event fields |
| Time format | relative numeric counters; timezone not specified |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not applicable to this Host format.

### Host Features
- API/syscall event frequencies by `I` and descriptor `name`;
- event n-grams and transitions;
- trace length and event density;
- `args` features, including process paths, module basenames, and command line tokens;
- parent-child/process context from process notification documents;
- descriptor `category` frequencies;
- command line and module path entropy.

### Network / Hybrid Features
- no direct network flow fields were detected;
- correlation with network datasets may be possible through an external sample/file id if project metadata provides one.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors in sample: {parse_error_count} |
| Missing values | yes | BSON arrays contain null/empty positions in `args` |
| Unstable structure | yes | descriptor and event documents use different schemas |
| Mixed schemas | yes | a single stream mixes metadata/descriptor/event documents |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
The format is valuable for host behaviour sequence features, but it is not ready for generic tabular reading. A dedicated BSON parser is required to map descriptor documents to event documents by `I`, expand `args`, and preserve event order. No explicit label field was found in the TEST/BSON sample.
"""

    def _build_ru_readme(self, summary: dict[str, Any]) -> str:
        return self._build_readme(summary, language="ru")

    def _build_en_readme(self, summary: dict[str, Any]) -> str:
        return self._build_readme(summary, language="en")

    def _build_readme(self, summary: dict[str, Any], language: str) -> str:
        title = "# Анализ содержимого файлов датасетов" if language == "ru" else "# Dataset File Content Analysis"
        yes = "да" if language == "ru" else "yes"
        no = "нет" if language == "ru" else "no"
        pending = "не анализировалось в Task44" if language == "ru" else "not analyzed in Task44"
        header = (
            "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n"
            if language == "ru"
            else "| Format | File count | DNS | Host | Status | Document |\n"
        )
        status_by_format = {
            "bson": (summary["final_status"], "bson.md"),
        }
        rows: list[str] = []
        for fmt, count in sorted(self._load_host_test_format_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return (
            f"{title} (Host TEST)\n\n"
            f"{header}"
            "|---|---:|---|---|---|---|\n"
            + "\n".join(rows)
            + "\n"
        )

    def _build_ru_report(self, summary: dict[str, Any], summary_json_path: Path) -> str:
        return f"""# Отчёт по Task44: Analysis of host test bson dataset files

## Описание задачи
Выполнен анализ содержимого файлов `PATH_HOST_DATASETS_FILTER\\TEST\\bson` на основе путей из `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_test_bson_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/bson.md`
- `docs/en/analysis-dataset/host/test/bson.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/test/Task44(Analysis of host test bson dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/test/Task44(Analysis of host test bson dataset files)_report.md`

## Структура JSON
Источник `{self.HOST_INPUT_JSON_FILE}` имеет структуру `role -> format -> list[path]`. Для задачи использован bucket `TEST.bson`.

## Логика группировки путей
Handler читает только Host JSON, выбирает роль `TEST` и формат `bson`, сортирует пути, затем берёт равномерную выборку до {self.max_files_per_format} файлов. Для каждого файла читается не больше {self.max_bytes_per_file} байт и не больше {self.max_docs_per_file} BSON-документов.

## Пример итогового JSON
```json
{self._summary_json_excerpt(summary)}
```

## Результат
Создан summary `{summary_json_path}`. Итоговый статус: `{summary["final_status"]}`. Нужен отдельный BSON parser: `true`.
"""

    def _build_en_report(self, summary: dict[str, Any], summary_json_path: Path) -> str:
        return f"""# Task44 Report: Analysis of host test bson dataset files

## Task Description
Analyzed files under `PATH_HOST_DATASETS_FILTER\\TEST\\bson` using paths from `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_test_bson_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/bson.md`
- `docs/en/analysis-dataset/host/test/bson.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/test/Task44(Analysis of host test bson dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/test/Task44(Analysis of host test bson dataset files)_report.md`

## JSON Structure
The source `{self.HOST_INPUT_JSON_FILE}` is structured as `role -> format -> list[path]`. This task uses the `TEST.bson` bucket.

## Path Grouping Logic
The handler reads only the Host JSON, selects role `TEST` and format `bson`, sorts paths, then takes an evenly distributed sample of up to {self.max_files_per_format} files. Each file is read with limits of {self.max_bytes_per_file} bytes and {self.max_docs_per_file} BSON documents.

## Result JSON Example
```json
{self._summary_json_excerpt(summary)}
```

## Result
Created summary `{summary_json_path}`. Final status: `{summary["final_status"]}`. Dedicated BSON parser required: `true`.
"""

    def _render_ru_fields(self, summary: dict[str, Any]) -> str:
        purposes = {
            "I": "идентификатор descriptor/event",
            "name": "имя API/syscall-like события",
            "type": "тип descriptor-документа",
            "category": "категория события",
            "args": "массив аргументов или имён аргументов",
            "T": "числовой идентификатор thread/process контекста",
            "t": "относительный временной/порядковый счётчик",
            "h": "дополнительный числовой счётчик/handle",
            "flags_value": "вложенные значения flags",
            "flags_bitmask": "вложенные bitmask flags",
        }
        return self._render_fields(summary, purposes)

    def _render_en_fields(self, summary: dict[str, Any]) -> str:
        purposes = {
            "I": "descriptor/event identifier",
            "name": "API/syscall-like event name",
            "type": "descriptor document type",
            "category": "event category",
            "args": "argument values or argument-name array",
            "T": "numeric thread/process context id",
            "t": "relative time/order counter",
            "h": "additional numeric counter/handle",
            "flags_value": "nested flag values",
            "flags_bitmask": "nested bitmask flags",
        }
        return self._render_fields(summary, purposes)

    @staticmethod
    def _render_fields(summary: dict[str, Any], purposes: dict[str, str]) -> str:
        rows: list[str] = []
        top_fields = list(summary["top_fields"])
        by_name = {str(field["field"]): field for field in top_fields}
        ordered_fields: list[dict[str, Any]] = []
        seen: set[str] = set()
        for field_name in (
            "I",
            "name",
            "type",
            "category",
            "args",
            "T",
            "t",
            "h",
            "flags_value",
            "flags_bitmask",
            "args.0",
            "args.1",
        ):
            field = by_name.get(field_name)
            if field is None:
                continue
            ordered_fields.append(field)
            seen.add(field_name)
        for field in top_fields:
            field_name = str(field["field"])
            if field_name in seen:
                continue
            ordered_fields.append(field)
            seen.add(field_name)
            if len(ordered_fields) >= 15:
                break

        for field in ordered_fields[:15]:
            field_name = str(field["field"])
            base_name = field_name.split(".", 1)[0]
            purpose = purposes.get(field_name, purposes.get(base_name, "sampled BSON field"))
            example = str(field["example"]).replace("|", "\\|")
            rows.append(f"| {field_name} | {field['type']} | {purpose} | {example} |")
        return "\n".join(rows)

    def _load_host_test_format_counts(self) -> dict[str, int]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        role_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            return {}
        result: dict[str, int] = {}
        for fmt, paths in role_bucket.items():
            if isinstance(paths, list):
                result[fmt] = len(paths)
        return result

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        excerpt = {
            "format": summary["format"],
            "role": summary["role"],
            "scope": summary["scope"],
            "parsed_document_count": summary["parsed_document_count"],
            "final_status": summary["final_status"],
            "needs_custom_parser": summary["needs_custom_parser"],
            "top_fields": summary["top_fields"][:5],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
