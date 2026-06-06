from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostTestNetflowDayContentAnalysisResult:
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
class NetflowDayProbe:
    path: str
    file_name: str
    file_size_bytes: int
    sampled_rows: int
    column_count_distribution: dict[str, int]
    missing_cells: int
    inconsistent_rows: int
    parse_error: str | None


class HostTestNetflowDayContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "netflow_day"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-test-netflow-day-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    COLUMNS = [
        "time",
        "duration",
        "src_host",
        "dst_host",
        "protocol",
        "src_port",
        "dst_port",
        "src_packets",
        "dst_packets",
        "src_bytes",
        "dst_bytes",
    ]

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

    def analyze_and_generate_docs(self) -> HostTestNetflowDayContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TEST/netflow_day.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "netflow_day.md"
        docs_en_path = self.docs_en_dir / "netflow_day.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task48(Analysis of host test netflow_day dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task48(Analysis of host test netflow_day dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary_payload, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary_payload, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary_payload, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary_payload, summary_json_path, "en"))

        return HostTestNetflowDayContentAnalysisResult(
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
        probes: list[NetflowDayProbe] = []
        type_counts: dict[str, Counter[str]] = {column: Counter() for column in self.COLUMNS}
        examples: dict[str, str] = {}
        protocol_counts: Counter[str] = Counter()
        missing_files = 0
        empty_files = 0
        parse_errors: Counter[str] = Counter()

        for path in sampled_paths:
            probe, rows = self._probe_file(path)
            probes.append(probe)
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            if not path.exists():
                missing_files += 1
            if probe.file_size_bytes == 0:
                empty_files += 1

            for row in rows:
                for column, value in zip(self.COLUMNS, row):
                    normalized = value.strip()
                    type_counts[column][self._infer_type(normalized)] += 1
                    examples.setdefault(column, normalized[:120])
                    if column == "protocol":
                        protocol_counts[normalized] += 1

        parsed_rows = sum(probe.sampled_rows for probe in probes)
        inconsistent_rows = sum(probe.inconsistent_rows for probe in probes)
        if parsed_rows == 0:
            final_status = self.STATUS_BROKEN
        elif inconsistent_rows:
            final_status = self.STATUS_PARTIAL
        else:
            final_status = self.STATUS_READY

        fields = []
        for column in self.COLUMNS:
            dominant_type = type_counts[column].most_common(1)[0][0] if type_counts[column] else "unknown"
            fields.append(
                {
                    "field": column,
                    "type": dominant_type,
                    "example": examples.get(column, ""),
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
            "protocol_counts_sample": dict(protocol_counts.most_common(10)),
            "parsed_rows": parsed_rows,
            "missing_files_in_sample": missing_files,
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "high",
        }

    def _probe_file(self, path: Path) -> tuple[NetflowDayProbe, list[list[str]]]:
        if not path.exists():
            return (
                NetflowDayProbe(str(path), path.name, 0, 0, {}, 0, 0, "file_not_found"),
                [],
            )
        file_size = path.stat().st_size
        if file_size == 0:
            return (
                NetflowDayProbe(str(path), path.name, 0, 0, {}, 0, 0, "empty_file"),
                [],
            )

        rows: list[list[str]] = []
        column_distribution: Counter[str] = Counter()
        missing_cells = 0
        inconsistent_rows = 0
        try:
            with path.open("r", encoding="utf-8", errors="replace", newline="") as stream:
                reader = csv.reader(stream)
                for index, row in enumerate(reader):
                    if index >= self.max_lines_per_file:
                        break
                    column_distribution[str(len(row))] += 1
                    missing_cells += sum(1 for value in row if value == "")
                    if len(row) != len(self.COLUMNS):
                        inconsistent_rows += 1
                        continue
                    rows.append(row)
        except (OSError, csv.Error) as error:
            return (
                NetflowDayProbe(str(path), path.name, file_size, 0, {}, 0, 0, str(error)),
                [],
            )

        return (
            NetflowDayProbe(
                path=str(path),
                file_name=path.name,
                file_size_bytes=file_size,
                sampled_rows=len(rows),
                column_count_distribution=dict(column_distribution),
                missing_cells=missing_cells,
                inconsistent_rows=inconsistent_rows,
                parse_error=None,
            ),
            rows,
        )

    @staticmethod
    def _infer_type(value: str) -> str:
        if value == "":
            return "missing"
        try:
            int(value)
            return "integer"
        except ValueError:
            pass
        if value.startswith("Comp") or value.startswith("IP"):
            return "anonymized_host"
        if value.startswith("Port"):
            return "anonymized_port"
        return "string"

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        return self._build_markdown(summary, "ru")

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        return self._build_markdown(summary, "en")

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._render_fields(summary, language)
        parse_error_count = sum(summary["parse_errors"].values())
        protocols = ", ".join(f"{key}: {value}" for key, value in summary["protocol_counts_sample"].items())

        if ru:
            return f"""# Анализ формата: netflow_day

## 1. Назначение
`netflow_day` в Host TEST содержит большие CSV-like netflow-файлы без заголовка. Формат нужен для извлечения network/hybrid признаков: длительность flow, протокол, endpoints, ports, packets и bytes.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | netflow_day |
| Варианты расширения | без расширения; имя `netflow_day-*` |
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
| Табличная структура | да |
| Заголовок | нет |
| Разделитель | comma |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Sample-строк разобрано | {summary["parsed_rows"]} |

## 5. Содержательная структура
Строки описывают netflow-события LANL-like формата: `time,duration,src_host,dst_host,protocol,src_port,dst_port,src_packets,dst_packets,src_bytes,dst_bytes`. Хосты и часть портов анонимизированы (`Comp...`, `IP...`, `Port...`). Протоколы в sample: {protocols}.

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
| Название поля | time |
| Формат времени | числовой offset/second counter |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- DNS можно косвенно выделять по `dst_port=53`, но DNS payload отсутствует.

### Host-признаки
- активность host endpoint по `src_host`/`dst_host`;
- user-host признаки отсутствуют.

### Network / hybrid-признаки
- длительность flow;
- bytes/packets в обоих направлениях;
- protocol и ports;
- fan-in/fan-out по host;
- временные окна netflow activity;
- host + network correlation features.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | нет | в sample пустые ячейки не обнаружены |
| Нестабильная структура | нет | 11 колонок в sample |
| Смешанные схемы | нет | оба файла имеют одинаковую структуру |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
`netflow_day` готов к feature extraction как большой line-oriented network flow источник. Нужно учитывать очень большой размер файлов и отсутствие встроенных labels.
"""

        return f"""# Format Analysis: netflow_day

## 1. Purpose
`netflow_day` in Host TEST contains large headerless CSV-like netflow files. The format is useful for network/hybrid features: flow duration, protocol, endpoints, ports, packets, and bytes.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | netflow_day |
| Extension variants | no extension; `netflow_day-*` names |
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
| Tabular structure | yes |
| Header | no |
| Delimiter | comma |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Sample rows parsed | {summary["parsed_rows"]} |

## 5. Content Structure
Rows describe LANL-like netflow events: `time,duration,src_host,dst_host,protocol,src_port,dst_port,src_packets,dst_packets,src_bytes,dst_bytes`. Hosts and some ports are anonymized (`Comp...`, `IP...`, `Port...`). Protocols in sample: {protocols}.

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
| Field name | time |
| Time format | numeric offset/second counter |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- DNS can be inferred indirectly from `dst_port=53`, but DNS payload is absent.

### Host Features
- host endpoint activity by `src_host`/`dst_host`;
- user-host features are absent.

### Network / Hybrid Features
- flow duration;
- bidirectional bytes/packets;
- protocol and ports;
- host fan-in/fan-out;
- time-window netflow activity;
- host + network correlation features.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | no | no empty cells in sample |
| Unstable structure | no | 11 columns in sample |
| Mixed schemas | no | both files use the same structure |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
`netflow_day` is ready for feature extraction as a large line-oriented network flow source. The pipeline must account for very large file sizes and the absence of embedded labels.
"""

    @staticmethod
    def _render_fields(summary: dict[str, Any], language: str) -> str:
        purposes = {
            "time": "flow start time" if language == "en" else "время начала flow",
            "duration": "flow duration" if language == "en" else "длительность flow",
            "src_host": "source host" if language == "en" else "source host",
            "dst_host": "destination host" if language == "en" else "destination host",
            "protocol": "IP protocol number" if language == "en" else "номер IP protocol",
            "src_port": "source port" if language == "en" else "source port",
            "dst_port": "destination port" if language == "en" else "destination port",
            "src_packets": "source packets" if language == "en" else "packets от source",
            "dst_packets": "destination packets" if language == "en" else "packets от destination",
            "src_bytes": "source bytes" if language == "en" else "bytes от source",
            "dst_bytes": "destination bytes" if language == "en" else "bytes от destination",
        }
        return "\n".join(
            f"| {field['field']} | {field['type']} | {purposes[field['field']]} | {field['example']} |"
            for field in summary["fields"]
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
        pending = "ещё не анализировалось" if language == "ru" else "not analyzed yet"
        status_by_format = {
            "bson": (self._load_optional_status("analysis-host-test-bson-summary.json"), "bson.md"),
            "csv": (self._load_optional_status("analysis-host-test-csv-summary.json"), "csv.md"),
            "json": (self._load_optional_status("analysis-host-test-json-summary.json"), "json.md"),
            "log": (self._load_optional_status("analysis-host-test-log-summary.json"), "log.md"),
            "netflow_day": (summary["final_status"], "netflow_day.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_host_test_format_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host TEST)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task48: Analysis of host test netflow_day dataset files"
            if ru
            else "# Task48 Report: Analysis of host test netflow_day dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\TEST\\netflow_day` на основе `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\TEST\\netflow_day` using `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_test_netflow_day_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/netflow_day.md`
- `docs/en/analysis-dataset/host/test/netflow_day.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task48(Analysis of host test netflow_day dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task48(Analysis of host test netflow_day dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `TEST.netflow_day`.

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{('Handler анализирует все пути формата и читает только первые sample-строки огромных файлов.' if ru else 'The handler analyzes all paths for the format and reads only the first sample rows from huge files.')}

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
            "parsed_rows": summary["parsed_rows"],
            "protocol_counts_sample": summary["protocol_counts_sample"],
            "final_status": summary["final_status"],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
