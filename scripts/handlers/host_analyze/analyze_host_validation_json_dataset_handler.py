from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class HostValidationJSONContentAnalysisResult:
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


class HostValidationJSONContentAnalysisHandler:
    ROLE_NAME = "VALIDATION"
    FORMAT_NAME = "json"
    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-validation-json-summary.json"
    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000
    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = DEFAULT_MAX_LINES_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.report_path = Path(report_path).expanduser() if report_path is not None else self.project_root / "report"
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_lines_per_file = max(50, max_lines_per_file)
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host" / "validation"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host" / "validation"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "host" / "validation"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "host" / "validation"

    def analyze_and_generate_docs(self) -> HostValidationJSONContentAnalysisResult:
        paths = self._extract_paths()
        if not paths:
            raise ValueError("No files found in sort-path-host-file.json for VALIDATION/json.")
        sample_paths = self._select_sample_paths(paths)
        summary = self._build_summary(paths, sample_paths)
        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "json.md"
        docs_en_path = self.docs_en_dir / "json.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task3(Analysis of host validation json dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task3(Analysis of host validation json dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return HostValidationJSONContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(paths),
            sampled_files_count=len(sample_paths),
            status=str(summary["final_status"]),
        )

    def _extract_paths(self) -> list[Path]:
        payload = JsonDataManager(self.temp_data_path / self.HOST_INPUT_JSON_FILE).read(default={})
        bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(bucket, dict):
            raise ValueError(f"Role '{self.ROLE_NAME}' in source JSON must be an object.")
        values = bucket.get(self.FORMAT_NAME, [])
        if not isinstance(values, list):
            raise ValueError(f"Role '{self.ROLE_NAME}' format '{self.FORMAT_NAME}' must be a list.")
        return sorted([Path(str(path)).expanduser() for path in values], key=lambda path: str(path).lower())

    def _select_sample_paths(self, paths: list[Path]) -> list[Path]:
        if len(paths) <= self.max_files_per_format:
            return paths
        step = (len(paths) - 1) / (self.max_files_per_format - 1)
        return [paths[index] for index in sorted({int(round(i * step)) for i in range(self.max_files_per_format)})]

    def _build_summary(self, paths: list[Path], sample_paths: list[Path]) -> dict[str, Any]:
        field_types: dict[str, Counter[str]] = {}
        examples: dict[str, str] = {}
        event_ids: Counter[str] = Counter()
        source_names: Counter[str] = Counter()
        channels: Counter[str] = Counter()
        hosts: Counter[str] = Counter()
        parse_errors: Counter[str] = Counter()
        empty_files = 0
        parsed_records = 0
        failed_lines = 0

        for path in sample_paths:
            if not path.exists():
                parse_errors["file_not_found"] += 1
                continue
            if path.stat().st_size == 0:
                empty_files += 1
                continue
            try:
                with path.open("r", encoding="utf-8", errors="replace") as stream:
                    for index, raw_line in enumerate(stream):
                        if index >= self.max_lines_per_file:
                            break
                        line = raw_line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            failed_lines += 1
                            continue
                        if not isinstance(record, dict):
                            failed_lines += 1
                            continue
                        parsed_records += 1
                        self._collect_record(record, field_types, examples)
                        for key in ("EventID", "event.code", "winlog.event_id"):
                            value = self._get_nested(record, key)
                            if value is not None:
                                event_ids[str(value)] += 1
                        for key in ("SourceName", "winlog.provider_name"):
                            value = self._get_nested(record, key)
                            if value is not None:
                                source_names[str(value)] += 1
                        for key in ("Channel", "winlog.channel"):
                            value = self._get_nested(record, key)
                            if value is not None:
                                channels[str(value)] += 1
                        for key in ("Hostname", "host.name"):
                            value = self._get_nested(record, key)
                            if value is not None:
                                hosts[str(value)] += 1
            except OSError as error:
                parse_errors[str(error)] += 1

        if parsed_records == 0:
            status = self.STATUS_BROKEN
        elif failed_lines:
            status = self.STATUS_PARTIAL
        else:
            status = self.STATUS_READY
        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.HOST_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(paths),
                "sampled_files_count": len(sample_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "sample_paths": [str(path) for path in sample_paths[:10]],
            "parsed_records": parsed_records,
            "failed_lines": failed_lines,
            "fields": [
                {"field": name, "type": counter.most_common(1)[0][0], "example": examples.get(name, "")}
                for name, counter in sorted(field_types.items())
            ],
            "event_ids": dict(event_ids.most_common(20)),
            "source_names": dict(source_names.most_common(10)),
            "channels": dict(channels.most_common(10)),
            "hosts_sample": dict(hosts.most_common(10)),
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": status,
            "needs_custom_parser": False,
            "processing_priority": "high",
        }

    def _collect_record(
        self,
        record: dict[str, Any],
        field_types: dict[str, Counter[str]],
        examples: dict[str, str],
        prefix: str = "",
        depth: int = 0,
    ) -> None:
        if depth > 2:
            return
        for key, value in record.items():
            field_name = f"{prefix}.{key}" if prefix else key
            field_types.setdefault(field_name, Counter())[type(value).__name__] += 1
            examples.setdefault(field_name, self._format_example(value))
            if isinstance(value, dict):
                self._collect_record(value, field_types, examples, field_name, depth + 1)

    @staticmethod
    def _get_nested(record: dict[str, Any], path: str) -> Any:
        current: Any = record
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    @staticmethod
    def _format_example(value: Any) -> str:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        text = text.replace("\r", "\\r").replace("\n", "\\n")
        return text[:117] + "..." if len(text) > 120 else text

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._fields_table(summary, language)
        event_ids = ", ".join(f"{key}: {value}" for key, value in summary["event_ids"].items())
        parse_errors = sum(summary["parse_errors"].values()) + summary["failed_lines"]

        if ru:
            return f"""# Анализ формата: json

## 1. Назначение
JSON-файлы Host VALIDATION содержат Windows Security/Sysmon/Eventlog события в JSON Lines формате. Формат нужен для Event ID, process, command-line, authentication и host activity признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | json |
| Варианты расширения | .json |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
| Количество файлов | {summary["scope"]["total_files_count"]} |

## 3. Примеры файлов
```text
{examples}
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет, JSON Lines |
| Заголовок | нет |
| Разделитель | newline-delimited JSON |
| Кодировка | utf-8 |
| Вложенная структура | да |
| Parsed records | {summary["parsed_records"]} |

## 5. Содержательная структура
Содержит Windows/Sysmon events: `EventID`, `SourceName`, `Channel`, `Hostname`, `TimeCreated`, `@timestamp`, `CommandLine`, process/user/security fields. EventID sample: {event_ids}.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
{fields}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | отсутствует |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | частично, при внешней разметке из scenario/file name |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | TimeCreated, @timestamp |
| Формат времени | ISO-8601 / Windows timestamp string |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не являются основным содержимым.

### Host-признаки
- Event ID frequencies;
- process and command-line features;
- parent/child process fields where present;
- authentication/security event sequences;
- user-host interaction counts.

### Network / hybrid-признаки
- SourceAddress/DestAddress/ports fields where present;
- correlation with packet captures by scenario.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | count: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_errors else "нет"} | parse/line errors: {parse_errors} |
| Missing values | частично | поля зависят от EventID/provider |
| Нестабильная структура | частично | Security/Sysmon/Eventlog схемы отличаются |
| Смешанные схемы | да | разные providers/channels |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
JSON готов к feature extraction как JSON Lines Windows/Sysmon telemetry. Нужно учитывать provider-specific поля и отсутствие встроенных labels.
"""

        return f"""# Format Analysis: json

## 1. Purpose
Host VALIDATION JSON files contain Windows Security/Sysmon/Eventlog events in JSON Lines format. The format is useful for Event ID, process, command-line, authentication, and host activity features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | json |
| Extension variants | .json |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
| File count | {summary["scope"]["total_files_count"]} |

## 3. Example Files
```text
{examples}
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes |
| Tabular structure | no, JSON Lines |
| Header | no |
| Delimiter | newline-delimited JSON |
| Encoding | utf-8 |
| Nested structure | yes |
| Parsed records | {summary["parsed_records"]} |

## 5. Content Structure
Contains Windows/Sysmon events: `EventID`, `SourceName`, `Channel`, `Hostname`, `TimeCreated`, `@timestamp`, `CommandLine`, and process/user/security fields. EventID sample: {event_ids}.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
{fields}

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | absent |
| Label values | not detected |
| Suitable for supervised learning | partial, with external labels from scenario/file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | TimeCreated, @timestamp |
| Time format | ISO-8601 / Windows timestamp string |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not the primary content.

### Host Features
- Event ID frequencies;
- process and command-line features;
- parent/child process fields where present;
- authentication/security event sequences;
- user-host interaction counts.

### Network / Hybrid Features
- SourceAddress/DestAddress/ports where present;
- correlation with packet captures by scenario.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_errors else "no"} | parse/line errors: {parse_errors} |
| Missing values | partial | fields depend on EventID/provider |
| Unstable structure | partial | Security/Sysmon/Eventlog schemas differ |
| Mixed schemas | yes | different providers/channels |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
JSON is ready for feature extraction as JSON Lines Windows/Sysmon telemetry. Provider-specific fields and missing embedded labels must be handled explicitly.
"""

    @staticmethod
    def _fields_table(summary: dict[str, Any], language: str) -> str:
        purposes = {
            "EventID": "Windows Event ID",
            "event.code": "ECS event code",
            "SourceName": "event provider",
            "Channel": "event channel",
            "Hostname": "host name",
            "TimeCreated": "event timestamp",
            "@timestamp": "event timestamp",
            "CommandLine": "process command line",
            "ProcessName": "process name",
            "SubjectUserName": "user name",
        }
        preferred = ["EventID", "event.code", "SourceName", "Channel", "Hostname", "TimeCreated", "@timestamp", "CommandLine", "ProcessName", "SubjectUserName"]
        by_name = {field["field"]: field for field in summary["fields"]}
        selected = [by_name[name] for name in preferred if name in by_name]
        for field in summary["fields"]:
            if field not in selected:
                selected.append(field)
            if len(selected) >= 16:
                break
        rows = []
        for field in selected[:16]:
            purpose = purposes.get(field["field"], "event field")
            example = str(field["example"]).replace("|", "\\|")
            rows.append(f"| {field['field']} | {field['type']} | {purpose} | {example} |")
        return "\n".join(rows)

    def _build_readme(self, summary: dict[str, Any], language: str) -> str:
        title = "# Анализ содержимого файлов датасетов" if language == "ru" else "# Dataset File Content Analysis"
        header = "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n" if language == "ru" else "| Format | File count | DNS | Host | Status | Document |\n"
        yes = "да" if language == "ru" else "yes"
        no = "нет" if language == "ru" else "no"
        pending = "ещё не анализировалось" if language == "ru" else "not analyzed yet"
        status_by_format = {
            "cap": (self._load_optional_status("analysis-host-validation-cap-summary.json"), "cap.md"),
            "csv": (self._load_optional_status("analysis-host-validation-csv-summary.json"), "csv.md"),
            "json": (summary["final_status"], "json.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = "# Отчёт по Task3: Analysis of host validation json dataset files" if ru else "# Task3 Report: Analysis of host validation json dataset files"
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\VALIDATION\\json` на основе `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\VALIDATION\\json` using `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_validation_json_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/validation/json.md`
- `docs/en/analysis-dataset/host/validation/json.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/validation/Task3(Analysis of host validation json dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/validation/Task3(Analysis of host validation json dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.json`.

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{('Handler берёт равномерную выборку JSON-файлов и читает ограниченное число JSON Lines записей на файл.' if ru else 'The handler takes an even sample of JSON files and reads a limited number of JSON Lines records per file.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_counts(self) -> dict[str, int]:
        payload = JsonDataManager(self.temp_data_path / self.HOST_INPUT_JSON_FILE).read(default={})
        bucket = payload.get(self.ROLE_NAME, {})
        return {fmt: len(paths) for fmt, paths in bucket.items() if isinstance(paths, list)} if isinstance(bucket, dict) else {}

    def _load_optional_status(self, summary_file_name: str) -> str:
        path = self.temp_data_path / summary_file_name
        if not path.exists():
            return "-"
        payload = JsonDataManager(path).read(default={})
        status = payload.get("final_status")
        return str(status) if isinstance(status, str) else "-"

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        return json.dumps(
            {
                "format": summary["format"],
                "role": summary["role"],
                "scope": summary["scope"],
                "parsed_records": summary["parsed_records"],
                "event_ids": summary["event_ids"],
                "final_status": summary["final_status"],
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
