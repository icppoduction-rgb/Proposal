from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostTestJSONContentAnalysisResult:
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
class JSONProbe:
    path: str
    file_name: str
    file_size_bytes: int
    sampled_lines: int
    parsed_records: int
    schema_kind: str
    parse_error: str | None


class HostTestJSONContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "json"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000
    DEFAULT_MAX_BYTES_PER_FILE = 2 * 1024 * 1024

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-test-json-summary.json"

    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    NUMBER_LONG_RE = re.compile(r"NumberLong\((-?\d+)\)")
    NUMBER_INT_RE = re.compile(r"NumberInt\((-?\d+)\)")
    KEY_RE = re.compile(r'"([A-Za-z0-9_.$-]+)"\s*:')

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = DEFAULT_MAX_LINES_PER_FILE,
        max_bytes_per_file: int = DEFAULT_MAX_BYTES_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.report_path = Path(report_path).expanduser() if report_path is not None else self.project_root / "report"
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_lines_per_file = max(50, max_lines_per_file)
        self.max_bytes_per_file = max(64 * 1024, max_bytes_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host" / "test"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host" / "test"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "host" / "test"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "host" / "test"

    def analyze_and_generate_docs(self) -> HostTestJSONContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TEST/json.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "json.md"
        docs_en_path = self.docs_en_dir / "json.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task46(Analysis of host test json dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task46(Analysis of host test json dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(summary_payload))
        self._write_text_file(report_ru_path, self._build_ru_report(summary_payload, summary_json_path))
        self._write_text_file(report_en_path, self._build_en_report(summary_payload, summary_json_path))

        return HostTestJSONContentAnalysisResult(
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
        probes: list[JSONProbe] = []
        field_types: Counter[tuple[str, str]] = Counter()
        schema_kinds: Counter[str] = Counter()
        event_names: Counter[str] = Counter()
        categories: Counter[str] = Counter()
        examples: dict[str, str] = {}
        parse_errors: Counter[str] = Counter()
        empty_files = 0

        for path in sampled_paths:
            probe, records, extracted_keys = self._probe_file(path)
            probes.append(probe)
            schema_kinds[probe.schema_kind] += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            if probe.file_size_bytes == 0:
                empty_files += 1

            for record in records:
                self._collect_record(record, field_types, event_names, categories, examples)
            for key in extracted_keys:
                field_types[(key, "unknown")] += 1

        parsed_records = sum(probe.parsed_records for probe in probes)
        final_status = self.STATUS_BROKEN if parsed_records == 0 and not field_types else self.STATUS_NEEDS_CUSTOM
        top_fields = [
            {
                "field": field,
                "type": type_name,
                "observed_count": count,
                "example": examples.get(field, ""),
            }
            for (field, type_name), count in field_types.most_common(40)
        ]

        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.HOST_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
                "max_bytes_per_file": self.max_bytes_per_file,
            },
            "sample_paths": [str(path) for path in sampled_paths[:10]],
            "file_probes": [probe.__dict__ for probe in probes],
            "schema_kinds": dict(schema_kinds),
            "parsed_records": parsed_records,
            "top_fields": top_fields,
            "top_event_names": dict(event_names.most_common(20)),
            "top_categories": dict(categories.most_common(20)),
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": final_status,
            "needs_custom_parser": True,
            "processing_priority": "high",
        }

    def _probe_file(self, path: Path) -> tuple[JSONProbe, list[dict[str, Any]], list[str]]:
        if not path.exists():
            return (
                JSONProbe(str(path), path.name, 0, 0, 0, "missing", "file_not_found"),
                [],
                [],
            )
        file_size = path.stat().st_size
        if file_size == 0:
            return (
                JSONProbe(str(path), path.name, 0, 0, 0, "empty", "empty_file"),
                [],
                [],
            )

        with path.open("r", encoding="utf-8", errors="replace") as stream:
            text = stream.read(self.max_bytes_per_file)
        lines = text.splitlines()[: self.max_lines_per_file]
        records: list[dict[str, Any]] = []
        extracted_keys: list[str] = []
        parse_failures = 0

        stripped_text = text.strip()
        if stripped_text.startswith("{") and stripped_text.endswith("}") and "\n" not in stripped_text:
            record = self._parse_json_like(stripped_text)
            if record is not None:
                records.append(record)

        if not records:
            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                if stripped_line.startswith("{") and stripped_line.endswith("}"):
                    record = self._parse_json_like(stripped_line)
                    if record is None:
                        parse_failures += 1
                        continue
                    records.append(record)
                else:
                    extracted_keys.extend(self.KEY_RE.findall(stripped_line))

        if records:
            schema_kind = self._classify_schema(path.name, records[0])
            parse_error = None if parse_failures == 0 else f"line_parse_failures={parse_failures}"
        elif extracted_keys:
            schema_kind = "multiline_json_document"
            parse_error = None
        else:
            schema_kind = "unparsed"
            parse_error = "json_parse_failed"

        return (
            JSONProbe(
                path=str(path),
                file_name=path.name,
                file_size_bytes=file_size,
                sampled_lines=len(lines),
                parsed_records=len(records),
                schema_kind=schema_kind,
                parse_error=parse_error,
            ),
            records[: self.max_lines_per_file],
            extracted_keys[:500],
        )

    def _parse_json_like(self, value: str) -> dict[str, Any] | None:
        normalized = self.NUMBER_LONG_RE.sub(r"\1", value)
        normalized = self.NUMBER_INT_RE.sub(r"\1", normalized)
        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    @staticmethod
    def _classify_schema(file_name: str, record: dict[str, Any]) -> str:
        keys = set(record)
        if {"path", "pids", "filepath"}.issubset(keys):
            return "file_artifact_json_lines"
        if {"I", "name", "type", "category", "args"}.issubset(keys):
            return "event_descriptor_json_lines"
        if {"I", "T", "t", "h", "args"}.issubset(keys):
            return "event_record_json_lines"
        if {"started_on", "duration", "sample_id", "status"}.issubset(keys):
            return "task_metadata_json"
        if file_name.startswith("report"):
            return "sandbox_report_json"
        if file_name.startswith("reboot"):
            return "reboot_event_json_lines"
        return "json_lines"

    def _collect_record(
        self,
        record: dict[str, Any],
        field_types: Counter[tuple[str, str]],
        event_names: Counter[str],
        categories: Counter[str],
        examples: dict[str, str],
        prefix: str = "",
        depth: int = 0,
    ) -> None:
        if depth > 2:
            return
        for key, value in record.items():
            field_name = f"{prefix}.{key}" if prefix else key
            type_name = type(value).__name__
            field_types[(field_name, type_name)] += 1
            if field_name not in examples and value not in (None, [], {}):
                examples[field_name] = self._format_example(value)
            if field_name == "name" and isinstance(value, str):
                event_names[value] += 1
            if field_name == "category" and isinstance(value, str):
                categories[value] += 1
            if isinstance(value, dict):
                self._collect_record(value, field_types, event_names, categories, examples, field_name, depth + 1)

    @staticmethod
    def _format_example(value: Any) -> str:
        if isinstance(value, str):
            text = value
        else:
            text = json.dumps(value, ensure_ascii=False)
        text = text.replace("\r", "\\r").replace("\n", "\\n")
        return text[:117] + "..." if len(text) > 120 else text

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        return self._build_markdown(summary, "ru")

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        return self._build_markdown(summary, "en")

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        title = "# Анализ формата: json" if ru else "# Format Analysis: json"
        purpose = (
            "JSON-файлы Host TEST содержат несколько схем malware sandbox telemetry: event traces, file artifact maps, reboot events, task metadata и большие sandbox reports."
            if ru
            else "Host TEST JSON files contain several malware sandbox telemetry schemas: event traces, file artifact maps, reboot events, task metadata, and large sandbox reports."
        )
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._render_fields(summary, language)
        schema_kinds = ", ".join(f"{key}: {value}" for key, value in summary["schema_kinds"].items())
        parse_error_count = sum(summary["parse_errors"].values())
        labels_text = "нет" if ru else "no"
        no_text = "нет" if ru else "no"
        yes_text = "да" if ru else "yes"

        if ru:
            return f"""{title}

## 1. Назначение
{purpose} Формат нужен для построения sequence-признаков, признаков файловых артефактов и контекстных признаков sandbox-задач.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | json |
| Варианты расширения | .json |
| DNS | нет |
| Host | да |
| Роли | TEST |
| Количество файлов | {summary["scope"]["total_files_count"]} |

## 3. Примеры файлов
```text
{examples}
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да, но не для всех файлов |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none |
| Кодировка | utf-8 |
| Вложенная структура | да |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Схемы sample | {schema_kinds} |

## 5. Содержательная структура
В sample обнаружены JSON Lines с событиями процессов/API (`I`, `T`, `t`, `h`, `args`), descriptor-документы (`name`, `type`, `category`), карты файловых артефактов (`path`, `pids`, `filepath`), reboot-события, task metadata с `$dt` timestamp и большие многострочные sandbox reports.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
{fields}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | {labels_text} |
| Название поля | отсутствует в sample |
| Значения label | не обнаружены |
| Можно использовать для supervised learning | нет для TEST; нужны внешние метки |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | `time`, `t`, `started_on.$dt`, `completed_on.$dt`, `clock` |
| Формат времени | числовые относительные поля и ISO-like `$dt` |
| Можно строить sequence | да |
| Можно применять sliding window | частично |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- прямые DNS-поля не обнаружены.

### Host-признаки
- частоты API/syscall-like событий по `I`/`name`;
- n-grams и переходы событий;
- категории sandbox events;
- признаки файловых артефактов по `path`, `filepath`, `pids`;
- длительность sandbox task и статусы выполнения;
- sequence по порядку JSONL events.

### Network / hybrid-признаки
- напрямую flow-поля не обнаружены;
- возможна корреляция с CSV/pcap по внешнему sample id.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | да | `filepath`, `owner`, `machine` могут быть null |
| Нестабильная структура | да | несколько схем в одном формате |
| Смешанные схемы | да | event, files, reboot, report, task |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | да |
| Приоритет обработки | высокий |

## 12. Вывод
JSON полезен для feature extraction, но требует отдельного parser: часть файлов является JSON Lines, часть содержит Mongo-style `NumberLong(...)`, часть является большими многострочными reports. Для TEST нет явных label-полей.
"""

        return f"""{title}

## 1. Purpose
{purpose} The format is useful for sequence features, file-artifact features, and sandbox task context features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | json |
| Extension variants | .json |
| DNS | no |
| Host | yes |
| Roles | TEST |
| File count | {summary["scope"]["total_files_count"]} |

## 3. Example Files
```text
{examples}
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line reading | yes, but not for every file |
| Tabular structure | no |
| Header | no |
| Delimiter | none |
| Encoding | utf-8 |
| Nested structure | yes |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Sample schemas | {schema_kinds} |

## 5. Content Structure
The sample contains JSON Lines with process/API events (`I`, `T`, `t`, `h`, `args`), descriptor documents (`name`, `type`, `category`), file artifact maps (`path`, `pids`, `filepath`), reboot events, task metadata with `$dt` timestamps, and large multiline sandbox reports.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
{fields}

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | {no_text} |
| Field name | absent in sample |
| Label values | not detected |
| Suitable for supervised learning | no for TEST; external labels are required |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | {yes_text} |
| Field name | `time`, `t`, `started_on.$dt`, `completed_on.$dt`, `clock` |
| Time format | numeric relative fields and ISO-like `$dt` |
| Can build sequences | yes |
| Can apply sliding windows | partial |

## 9. Potential Feature Extraction
### DNS Features
- direct DNS fields were not detected.

### Host Features
- API/syscall-like event frequencies by `I`/`name`;
- event n-grams and transitions;
- sandbox event categories;
- file artifact features from `path`, `filepath`, and `pids`;
- sandbox task duration and execution status;
- sequence features by JSONL event order.

### Network / Hybrid Features
- direct flow fields were not detected;
- correlation with CSV/pcap may be possible through an external sample id.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | yes | `filepath`, `owner`, and `machine` may be null |
| Unstable structure | yes | several schemas share the same extension |
| Mixed schemas | yes | event, files, reboot, report, task |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | yes |
| Processing priority | high |

## 12. Conclusion
JSON is useful for feature extraction, but it needs a dedicated parser: some files are JSON Lines, some use Mongo-style `NumberLong(...)`, and some are large multiline reports. No explicit label field was found for TEST.
"""

    def _build_ru_readme(self, summary: dict[str, Any]) -> str:
        return self._build_readme(summary, "ru")

    def _build_en_readme(self, summary: dict[str, Any]) -> str:
        return self._build_readme(summary, "en")

    def _build_readme(self, summary: dict[str, Any], language: str) -> str:
        title = "# Анализ содержимого файлов датасетов" if language == "ru" else "# Dataset File Content Analysis"
        header = (
            "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n"
            if language == "ru"
            else "| Format | File count | DNS | Host | Status | Document |\n"
        )
        yes = "да" if language == "ru" else "yes"
        no = "нет" if language == "ru" else "no"
        pending = "ещё не анализировалось" if language == "ru" else "not analyzed yet"
        status_by_format = {
            "bson": (self._load_optional_status("analysis-host-test-bson-summary.json"), "bson.md"),
            "csv": (self._load_optional_status("analysis-host-test-csv-summary.json"), "csv.md"),
            "json": (summary["final_status"], "json.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_host_test_format_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host TEST)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_ru_report(self, summary: dict[str, Any], summary_json_path: Path) -> str:
        return self._build_report(summary, summary_json_path, "ru")

    def _build_en_report(self, summary: dict[str, Any], summary_json_path: Path) -> str:
        return self._build_report(summary, summary_json_path, "en")

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task46: Analysis of host test json dataset files"
            if ru
            else "# Task46 Report: Analysis of host test json dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\TEST\\json` на основе `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\TEST\\json` using `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        json_structure = (
            f"Источник `{self.HOST_INPUT_JSON_FILE}` имеет структуру `role -> format -> list[path]`; использован bucket `TEST.json`."
            if ru
            else f"The source `{self.HOST_INPUT_JSON_FILE}` is structured as `role -> format -> list[path]`; this task uses `TEST.json`."
        )
        grouping = (
            f"Handler сортирует пути, берёт равномерную выборку до {self.max_files_per_format} файлов и читает до {self.max_lines_per_file} строк / {self.max_bytes_per_file} байт на файл."
            if ru
            else f"The handler sorts paths, takes an even sample of up to {self.max_files_per_format} files, and reads up to {self.max_lines_per_file} lines / {self.max_bytes_per_file} bytes per file."
        )
        result = (
            f"Создан summary `{summary_json_path}`. Итоговый статус: `{summary['final_status']}`."
            if ru
            else f"Created summary `{summary_json_path}`. Final status: `{summary['final_status']}`."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_test_json_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/json.md`
- `docs/en/analysis-dataset/host/test/json.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/test/Task46(Analysis of host test json dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/test/Task46(Analysis of host test json dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
{json_structure}

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{grouping}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{result}
"""

    @staticmethod
    def _render_fields(summary: dict[str, Any], language: str) -> str:
        purposes = {
            "I": "event/descriptor id" if language == "en" else "идентификатор event/descriptor",
            "name": "event name" if language == "en" else "имя события",
            "type": "event type" if language == "en" else "тип события",
            "category": "event category" if language == "en" else "категория события",
            "args": "arguments" if language == "en" else "аргументы",
            "path": "artifact path" if language == "en" else "путь артефакта",
            "pids": "related process ids" if language == "en" else "связанные process ids",
            "filepath": "original file path" if language == "en" else "исходный путь файла",
            "started_on.$dt": "task start timestamp" if language == "en" else "время старта task",
            "duration": "task duration" if language == "en" else "длительность task",
            "sample_id": "sample id" if language == "en" else "идентификатор sample",
        }
        preferred = [
            "I",
            "name",
            "type",
            "category",
            "args",
            "T",
            "t",
            "h",
            "time",
            "path",
            "pids",
            "filepath",
            "started_on.$dt",
            "duration",
            "sample_id",
            "status",
        ]
        by_name = {field["field"]: field for field in summary["top_fields"]}
        selected = [by_name[name] for name in preferred if name in by_name]
        for field in summary["top_fields"]:
            if field not in selected:
                selected.append(field)
            if len(selected) >= 18:
                break
        rows = []
        for field in selected[:18]:
            name = str(field["field"])
            purpose = purposes.get(name, "sampled JSON field" if language == "en" else "поле sample JSON")
            example = str(field["example"]).replace("|", "\\|")
            rows.append(f"| {name} | {field['type']} | {purpose} | {example} |")
        return "\n".join(rows)

    def _load_host_test_format_counts(self) -> dict[str, int]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        role_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            return {}
        return {fmt: len(paths) for fmt, paths in role_bucket.items() if isinstance(paths, list)}

    def _load_optional_status(self, summary_file_name: str) -> str:
        summary_path = self.temp_data_path / summary_file_name
        if not summary_path.exists():
            return "-"
        try:
            payload = JsonDataManager(summary_path).read(default={})
        except (TypeError, ValueError):
            return "-"
        value = payload.get("final_status")
        return str(value) if isinstance(value, str) else "-"

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        excerpt = {
            "format": summary["format"],
            "role": summary["role"],
            "scope": summary["scope"],
            "schema_kinds": summary["schema_kinds"],
            "final_status": summary["final_status"],
            "top_fields": summary["top_fields"][:5],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
