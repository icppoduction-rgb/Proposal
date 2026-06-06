from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostTestWLSDayContentAnalysisResult:
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
class WLSDayProbe:
    path: str
    file_name: str
    file_size_bytes: int
    sampled_lines: int
    parsed_records: int
    parse_error: str | None


class HostTestWLSDayContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "wls_day"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-test-wls-day-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = DEFAULT_MAX_LINES_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_lines_per_file = max(50, max_lines_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host" / "test"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host" / "test"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "analysis-dataset" / "host" / "test"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "analysis-dataset" / "host" / "test"

    def analyze_and_generate_docs(self) -> HostTestWLSDayContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TEST/wls_day.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "wls_day.md"
        docs_en_path = self.docs_en_dir / "wls_day.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task50(Analysis of host test wls_day dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task50(Analysis of host test wls_day dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary_payload, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary_payload, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary_payload, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary_payload, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary_payload, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary_payload, summary_json_path, "en"))

        return HostTestWLSDayContentAnalysisResult(
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
        return all_paths[: self.max_files_per_format]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        probes: list[WLSDayProbe] = []
        field_types: dict[str, Counter[str]] = {}
        examples: dict[str, str] = {}
        event_ids: Counter[str] = Counter()
        logon_types: Counter[str] = Counter()
        auth_packages: Counter[str] = Counter()
        process_names: Counter[str] = Counter()
        parse_errors: Counter[str] = Counter()
        empty_files = 0

        for path in sampled_paths:
            probe, records = self._probe_file(path)
            probes.append(probe)
            if probe.file_size_bytes == 0:
                empty_files += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1

            for record in records:
                for key, value in record.items():
                    field_types.setdefault(key, Counter())[type(value).__name__] += 1
                    examples.setdefault(key, self._format_example(value))
                if "EventID" in record:
                    event_ids[str(record["EventID"])] += 1
                if "LogonType" in record:
                    logon_types[str(record["LogonType"])] += 1
                if "AuthenticationPackage" in record:
                    auth_packages[str(record["AuthenticationPackage"])] += 1
                if "ProcessName" in record:
                    process_names[str(record["ProcessName"])] += 1

        parsed_records = sum(probe.parsed_records for probe in probes)
        if parsed_records == 0:
            final_status = self.STATUS_BROKEN
        elif parse_errors:
            final_status = self.STATUS_PARTIAL
        else:
            final_status = self.STATUS_READY

        fields = []
        for field_name, counter in sorted(field_types.items()):
            fields.append(
                {
                    "field": field_name,
                    "type": counter.most_common(1)[0][0],
                    "example": examples.get(field_name, ""),
                }
            )

        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.HOST_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "sample_paths": [str(path) for path in sampled_paths],
            "file_probes": [probe.__dict__ for probe in probes],
            "fields": fields,
            "parsed_records": parsed_records,
            "event_ids": dict(event_ids.most_common(20)),
            "logon_types": dict(logon_types.most_common(20)),
            "auth_packages": dict(auth_packages.most_common(20)),
            "process_names": dict(process_names.most_common(20)),
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "high",
        }

    def _probe_file(self, path: Path) -> tuple[WLSDayProbe, list[dict[str, Any]]]:
        if not path.exists():
            return WLSDayProbe(str(path), path.name, 0, 0, 0, "file_not_found"), []
        file_size = path.stat().st_size
        if file_size == 0:
            return WLSDayProbe(str(path), path.name, 0, 0, 0, "empty_file"), []

        records: list[dict[str, Any]] = []
        parse_error: str | None = None
        sampled_lines = 0
        try:
            with path.open("r", encoding="utf-8", errors="replace") as stream:
                for index, raw_line in enumerate(stream):
                    if index >= self.max_lines_per_file:
                        break
                    sampled_lines += 1
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        value = json.loads(line)
                    except json.JSONDecodeError as error:
                        parse_error = f"json_decode_error:{error.msg}"
                        continue
                    if isinstance(value, dict):
                        records.append(value)
        except OSError as error:
            return WLSDayProbe(str(path), path.name, file_size, sampled_lines, 0, str(error)), []

        return (
            WLSDayProbe(
                path=str(path),
                file_name=path.name,
                file_size_bytes=file_size,
                sampled_lines=sampled_lines,
                parsed_records=len(records),
                parse_error=parse_error,
            ),
            records,
        )

    @staticmethod
    def _format_example(value: Any) -> str:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        text = text.replace("\r", "\\r").replace("\n", "\\n")
        return text[:117] + "..." if len(text) > 120 else text

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._render_fields(summary, language)
        event_ids = ", ".join(f"{key}: {value}" for key, value in summary["event_ids"].items())
        parse_error_count = sum(summary["parse_errors"].values())

        if ru:
            return f"""# Анализ формата: wls_day

## 1. Назначение
`wls_day` в Host TEST содержит Windows security log events в JSON Lines формате. Формат нужен для Event ID частот, authentication/logon последовательностей, parent-child process chains и user-host interaction признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | wls_day |
| Варианты расширения | без расширения; имя `wls_day-*` |
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
| Чтение построчно | да |
| Табличная структура | нет, JSON Lines |
| Заголовок | нет |
| Разделитель | newline-delimited JSON |
| Кодировка | utf-8 |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Parsed records | {summary["parsed_records"]} |

## 5. Содержательная структура
Строки содержат Windows security events: `EventID`, `UserName`, `LogHost`, `DomainName`, `LogonID`, `Time`, process fields и authentication/logon fields. EventID distribution in sample: {event_ids}.

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
| Можно использовать для supervised learning | нет без внешних меток |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | Time |
| Формат времени | числовой day/second offset |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- частоты Event ID;
- login success/failure и logon type ratios;
- user-host interaction frequency;
- authentication package distribution;
- parent-child process chains;
- process name frequencies;
- event sequences и sliding windows.

### Network / hybrid-признаки
- source/loghost interaction graph по `Source` и `LogHost`;
- host + network correlation features при наличии внешних netflow данных.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | частично | поля зависят от EventID |
| Нестабильная структура | частично | разные EventID имеют разные поля |
| Смешанные схемы | частично | 4624/4634/4672/4688 и другие события |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
`wls_day` готов к feature extraction для Windows/Sysmon-like authentication и process event признаков. Нужно учитывать огромный размер файлов и event-specific schema.
"""

        return f"""# Format Analysis: wls_day

## 1. Purpose
`wls_day` in Host TEST contains Windows security log events in JSON Lines format. The format is useful for Event ID frequencies, authentication/logon sequences, parent-child process chains, and user-host interaction features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | wls_day |
| Extension variants | no extension; `wls_day-*` names |
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
| Line-by-line reading | yes |
| Tabular structure | no, JSON Lines |
| Header | no |
| Delimiter | newline-delimited JSON |
| Encoding | utf-8 |
| Nested structure | no |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Parsed records | {summary["parsed_records"]} |

## 5. Content Structure
Rows contain Windows security events: `EventID`, `UserName`, `LogHost`, `DomainName`, `LogonID`, `Time`, process fields, and authentication/logon fields. EventID distribution in sample: {event_ids}.

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
| Suitable for supervised learning | no without external labels |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | Time |
| Time format | numeric day/second offset |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not applicable.

### Host Features
- Event ID frequencies;
- login success/failure and logon type ratios;
- user-host interaction frequency;
- authentication package distribution;
- parent-child process chains;
- process name frequencies;
- event sequences and sliding windows.

### Network / Hybrid Features
- source/loghost interaction graph from `Source` and `LogHost`;
- host + network correlation features when external netflow data is available.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | partial | fields depend on EventID |
| Unstable structure | partial | different EventIDs expose different fields |
| Mixed schemas | partial | 4624/4634/4672/4688 and other events |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
`wls_day` is ready for Windows/Sysmon-like authentication and process event feature extraction. The pipeline must account for huge file sizes and event-specific schemas.
"""

    @staticmethod
    def _render_fields(summary: dict[str, Any], language: str) -> str:
        purposes = {
            "Time": "event time offset" if language == "en" else "время события",
            "EventID": "Windows Event ID" if language == "en" else "Windows Event ID",
            "UserName": "user/account" if language == "en" else "user/account",
            "LogHost": "logging host" if language == "en" else "logging host",
            "LogonID": "logon session id" if language == "en" else "logon session id",
            "DomainName": "domain" if language == "en" else "domain",
            "ProcessName": "process name" if language == "en" else "process name",
            "ParentProcessName": "parent process" if language == "en" else "parent process",
            "Source": "source host" if language == "en" else "source host",
            "AuthenticationPackage": "auth package" if language == "en" else "auth package",
            "LogonType": "logon type" if language == "en" else "logon type",
        }
        preferred = [
            "Time",
            "EventID",
            "UserName",
            "LogHost",
            "DomainName",
            "LogonID",
            "LogonType",
            "LogonTypeDescription",
            "AuthenticationPackage",
            "Source",
            "ProcessName",
            "ProcessID",
            "ParentProcessName",
            "ParentProcessID",
        ]
        by_name = {field["field"]: field for field in summary["fields"]}
        selected = [by_name[name] for name in preferred if name in by_name]
        for field in summary["fields"]:
            if field not in selected:
                selected.append(field)
            if len(selected) >= 18:
                break
        return "\n".join(
            f"| {field['field']} | {field['type']} | {purposes.get(field['field'], 'event-specific field' if language == 'en' else 'event-specific field')} | {str(field['example']).replace('|', '\\|')} |"
            for field in selected[:18]
        )

    def _build_readme(self, summary: dict[str, Any], language: str) -> str:
        title = "# Анализ содержимого файлов датасетов" if language == "ru" else "# Dataset File Content Analysis"
        header = (
            "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n"
            if language == "ru"
            else "| Format | File count | DNS | Host | Status | Document |\n"
        )
        yes = "да" if language == "ru" else "yes"
        no = "нет" if language == "ru" else "no"
        status_by_format = {
            "bson": (self._load_optional_status("analysis-host-test-bson-summary.json"), "bson.md"),
            "csv": (self._load_optional_status("analysis-host-test-csv-summary.json"), "csv.md"),
            "json": (self._load_optional_status("analysis-host-test-json-summary.json"), "json.md"),
            "log": (self._load_optional_status("analysis-host-test-log-summary.json"), "log.md"),
            "netflow_day": (self._load_optional_status("analysis-host-test-netflow-day-summary.json"), "netflow_day.md"),
            "txt": (self._load_optional_status("analysis-host-test-txt-summary.json"), "txt.md"),
            "wls_day": (summary["final_status"], "wls_day.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_host_test_format_counts().items()):
            status, document = status_by_format.get(fmt, ("-", "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host TEST)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task50: Analysis of host test wls_day dataset files"
            if ru
            else "# Task50 Report: Analysis of host test wls_day dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\TEST\\wls_day` на основе `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\TEST\\wls_day` using `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_test_wls_day_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/wls_day.md`
- `docs/en/analysis-dataset/host/test/wls_day.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task50(Analysis of host test wls_day dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task50(Analysis of host test wls_day dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `TEST.wls_day`.

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{('Handler анализирует все 3 файла и читает ограниченное число JSON Lines записей на файл.' if ru else 'The handler analyzes all 3 files and reads a limited number of JSON Lines records per file.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

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
            "parsed_records": summary["parsed_records"],
            "event_ids": summary["event_ids"],
            "final_status": summary["final_status"],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
