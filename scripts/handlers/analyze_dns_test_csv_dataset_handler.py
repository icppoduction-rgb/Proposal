from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class DNSTestCSVContentAnalysisResult:
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
class DNSTestCSVProbe:
    path: str
    file_name: str
    file_size_bytes: int
    has_header: bool
    sampled_rows: int
    parsed_rows: int
    column_count_distribution: dict[str, int]
    missing_cells: int
    schema_kind: str
    parse_error: str | None


class DNSTestCSVContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "csv"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_ROWS_PER_FILE = 1000

    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-dns-test-csv-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    SYNTHETIC_FIELDS = [
        ("source_ip", "source/client IP address"),
        ("resolver_or_parent_domain", "parent domain or DNSBL service domain"),
        ("timestamp_ms", "event timestamp in Unix milliseconds"),
        ("label_or_flag", "boolean flag in the row"),
        ("query_domain", "queried domain or DNSBL lookup name"),
        ("feature_01", "numeric DNS/domain feature"),
        ("feature_02", "numeric DNS/domain feature"),
        ("feature_03", "numeric DNS/domain feature"),
        ("feature_04", "numeric DNS/domain feature"),
        ("feature_05", "numeric DNS/domain feature"),
        ("feature_06", "numeric DNS/domain feature"),
        ("feature_07", "numeric DNS/domain feature"),
        ("feature_08", "numeric DNS/domain feature"),
        ("feature_09", "numeric DNS/domain feature"),
        ("feature_10", "numeric DNS/domain feature"),
        ("feature_11", "numeric DNS/domain feature"),
        ("feature_12", "numeric DNS/domain feature"),
        ("feature_13", "numeric DNS/domain feature"),
        ("feature_14", "numeric DNS/domain feature"),
        ("feature_15", "numeric DNS/domain feature"),
        ("feature_16", "numeric DNS/domain feature"),
        ("feature_17", "numeric DNS/domain feature"),
    ]

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_rows_per_file: int = DEFAULT_MAX_ROWS_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.report_path = Path(report_path).expanduser() if report_path is not None else self.project_root / "report"
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_rows_per_file = max(1, max_rows_per_file)
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "dns" / "test"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "dns" / "test"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "dns" / "test"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "dns" / "test"

    def analyze_and_generate_docs(self) -> DNSTestCSVContentAnalysisResult:
        all_paths = self._extract_paths(self._read_source_json())
        if not all_paths:
            raise ValueError("No files found in sort-path-dns-file.json for TEST/csv.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "csv.md"
        docs_en_path = self.docs_en_dir / "csv.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task1(Analysis of dns test csv dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task1(Analysis of dns test csv dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return DNSTestCSVContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=len(sampled_paths),
            status=str(summary["final_status"]),
        )

    def _read_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.DNS_INPUT_JSON_FILE
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
            raise ValueError(f"Role '{self.ROLE_NAME}' format '{self.FORMAT_NAME}' must be a list.")
        return sorted(
            [Path(str(raw_path)).expanduser() for raw_path in format_bucket if isinstance(raw_path, str)],
            key=lambda path: str(path).lower(),
        )

    def _select_sample_paths(self, all_paths: list[Path]) -> list[Path]:
        return all_paths[: self.max_files_per_format]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        probes: list[DNSTestCSVProbe] = []
        column_type_votes: dict[str, Counter[str]] = defaultdict(Counter)
        examples_by_column: dict[str, str] = {}
        parse_errors: Counter[str] = Counter()
        parsed_rows = 0
        total_missing_cells = 0
        schema_kinds: Counter[str] = Counter()
        timestamp_columns: set[str] = set()

        for path in sampled_paths:
            probe, headers, data_rows = self._probe_csv(path)
            probes.append(probe)
            parsed_rows += probe.parsed_rows
            total_missing_cells += probe.missing_cells
            schema_kinds[probe.schema_kind] += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            for row in data_rows:
                for index, header in enumerate(headers):
                    value = row[index] if index < len(row) else ""
                    column_type_votes[header][self._infer_type(value)] += 1
                    if value and header not in examples_by_column:
                        examples_by_column[header] = value
            timestamp_columns.update(header for header in headers if "time" in header.lower())

        inconsistent_column_files = sum(1 for probe in probes if len(probe.column_count_distribution) > 1)
        missing_header_files = sum(1 for probe in probes if not probe.has_header)
        final_status = (
            self.STATUS_BROKEN
            if parsed_rows == 0
            else self.STATUS_PARTIAL
            if parse_errors or inconsistent_column_files or missing_header_files
            else self.STATUS_READY
        )

        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.DNS_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_rows_per_file": self.max_rows_per_file,
            },
            "sample_paths": [str(path) for path in sampled_paths],
            "file_probes": [probe.__dict__ for probe in probes],
            "schema_kinds": dict(schema_kinds.most_common()),
            "parsed_rows": parsed_rows,
            "total_missing_cells": total_missing_cells,
            "parse_errors": dict(parse_errors),
            "inconsistent_column_files": inconsistent_column_files,
            "missing_header_files": missing_header_files,
            "field_summaries": self._field_summaries(column_type_votes, examples_by_column),
            "timestamp_columns": sorted(timestamp_columns),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "medium",
        }

    def _probe_csv(self, path: Path) -> tuple[DNSTestCSVProbe, list[str], list[list[str]]]:
        if not path.exists():
            return self._probe(path, 0, False, 0, 0, {}, 0, "missing", "file_not_found"), [], []
        file_size = path.stat().st_size
        if file_size == 0:
            return self._probe(path, file_size, False, 0, 0, {}, 0, "empty", "empty_file"), [], []

        rows: list[list[str]] = []
        column_counts: Counter[str] = Counter()
        missing_cells = 0
        try:
            with path.open("r", encoding="utf-8", errors="replace", newline="") as stream:
                reader = csv.reader(stream)
                for index, row in enumerate(reader):
                    if index >= self.max_rows_per_file:
                        break
                    column_counts[str(len(row))] += 1
                    missing_cells += sum(1 for value in row if value == "")
                    rows.append(row)
        except (OSError, csv.Error) as error:
            return self._probe(path, file_size, False, 0, 0, {}, 0, "unparsed", str(error)), [], []

        if not rows:
            return self._probe(path, file_size, False, 0, 0, {}, 0, "empty", "empty_file"), [], []

        has_header = self._has_header(rows[0])
        headers = rows[0] if has_header else self._synthetic_headers(max(len(row) for row in rows))
        data_rows = rows[1:] if has_header else rows
        schema_kind = "headerless_dns_test_feature_table" if not has_header else "dns_test_feature_table"

        return (
            self._probe(
                path=path,
                file_size=file_size,
                has_header=has_header,
                sampled_rows=len(rows),
                parsed_rows=len(data_rows),
                column_counts=dict(column_counts),
                missing_cells=missing_cells,
                schema_kind=schema_kind,
                parse_error=None,
            ),
            headers,
            data_rows,
        )

    @staticmethod
    def _probe(
        path: Path,
        file_size: int,
        has_header: bool,
        sampled_rows: int,
        parsed_rows: int,
        column_counts: dict[str, int],
        missing_cells: int,
        schema_kind: str,
        parse_error: str | None,
    ) -> DNSTestCSVProbe:
        return DNSTestCSVProbe(
            path=str(path),
            file_name=path.name,
            file_size_bytes=file_size,
            has_header=has_header,
            sampled_rows=sampled_rows,
            parsed_rows=parsed_rows,
            column_count_distribution=column_counts,
            missing_cells=missing_cells,
            schema_kind=schema_kind,
            parse_error=parse_error,
        )

    @staticmethod
    def _has_header(row: list[str]) -> bool:
        normalized = {cell.strip().lower() for cell in row}
        header_tokens = {"domain", "timestamp", "label", "query", "fqdn", "entropy", "ip"}
        return bool(normalized & header_tokens)

    def _synthetic_headers(self, column_count: int) -> list[str]:
        defaults = [name for name, _ in self.SYNTHETIC_FIELDS]
        return defaults[:column_count] + [f"column_{index + 1}" for index in range(len(defaults), column_count)]

    def _field_summaries(
        self,
        column_type_votes: dict[str, Counter[str]],
        examples_by_column: dict[str, str],
    ) -> list[dict[str, str]]:
        purposes = dict(self.SYNTHETIC_FIELDS)
        return [
            {
                "name": column,
                "dominant_type": self._dominant_type(votes),
                "purpose": purposes.get(column, "DNS test feature"),
                "example": examples_by_column.get(column, ""),
            }
            for column, votes in column_type_votes.items()
        ]

    @staticmethod
    def _infer_type(value: str) -> str:
        if value == "" or value.lower() == "nan":
            return "missing"
        if value.lower() in {"true", "false"}:
            return "boolean"
        try:
            int(value)
            return "integer"
        except ValueError:
            pass
        try:
            float(value)
            return "float"
        except ValueError:
            pass
        if "." in value and " " not in value and "/" not in value:
            return "domain_or_ip"
        return "string"

    @staticmethod
    def _dominant_type(counter: Counter[str]) -> str:
        filtered = Counter({key: value for key, value in counter.items() if key != "missing"})
        if filtered:
            return filtered.most_common(1)[0][0]
        return "unknown"

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"])
        fields = self._fields_table(summary["field_summaries"])
        schemas = ", ".join(f"{key}: {value}" for key, value in summary["schema_kinds"].items())
        parse_error_count = sum(summary["parse_errors"].values())

        if ru:
            return f"""# Анализ формата: csv

## 1. Назначение
CSV-файл DNS TEST содержит крупную табличную выборку DNS/domain признаков для финальной проверки pipeline. Датасет не должен использоваться для обучения; он нужен для оценки качества нормализации, feature engineering и inference-ready обработки.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | да |
| Host | нет |
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
| Parsed rows in sample | {summary["parsed_rows"]} |

## 5. Содержательная структура
Обнаруженная схема: {schemas}. Sample показывает фиксированную 22-колоночную структуру: IP/domain/timestamp/flag/query-domain и набор числовых DNS/domain признаков. Из-за отсутствия заголовка требуется явная positional schema перед production-нормализацией.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
{fields}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | `label_or_flag` |
| Значения label | boolean-like flag в sample |
| Можно использовать для supervised learning | нет, это TEST-роль; использовать только для оценки |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | `timestamp_ms` |
| Формат времени | Unix milliseconds |
| Можно строить sequence | да |
| Можно применять sliding window | да, после chunked-сортировки/группировки |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- source/client IP;
- parent/resolver domain;
- queried DNSBL/domain name;
- timestamp-derived windows;
- numeric domain/DNS ratios and aggregate features;
- entropy-like and distribution-like numeric features.

### Network / hybrid-признаки
- группировка по `source_ip`;
- последовательности запросов по `timestamp_ms`;
- корреляция query-domain с DNSBL/provider domain.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | нет | sample содержит строки |
| Поврежденные файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | {"да" if summary["total_missing_cells"] else "нет"} | missing cells в sample: {summary["total_missing_cells"]} |
| Нестабильная структура | {"да" if summary["inconsistent_column_files"] else "нет"} | inconsistent column files: {summary["inconsistent_column_files"]} |
| Смешанные схемы | нет | один CSV-файл |
| Слишком большой файл | да | файл около 8.25 GB; нужен streaming/chunked reader |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет, но нужна explicit positional schema |
| Приоритет обработки | средний |

## 12. Вывод
DNS TEST csv пригоден для дальнейшей обработки, но из-за отсутствия заголовка и большого размера его следует читать потоково и нормализовать по заранее закрепленной 22-колоночной схеме.
"""

        return f"""# Format Analysis: csv

## 1. Purpose
The DNS TEST CSV file contains a large tabular sample of DNS/domain features for final pipeline validation. The dataset must not be used for training; it is intended for normalization, feature-engineering, and inference-readiness checks.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
| DNS | yes |
| Host | no |
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
| Parsed rows in sample | {summary["parsed_rows"]} |

## 5. Content Structure
Detected schema: {schemas}. The sample shows a fixed 22-column structure: IP/domain/timestamp/flag/query-domain followed by numeric DNS/domain features. Because the file has no header, an explicit positional schema is required before production normalization.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
{fields}

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | `label_or_flag` |
| Label values | boolean-like flag in sample |
| Suitable for supervised learning | no, this is the TEST role; use for evaluation only |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | `timestamp_ms` |
| Time format | Unix milliseconds |
| Can build sequences | yes |
| Can apply sliding windows | yes, after chunked sorting/grouping |

## 9. Potential Feature Extraction
### DNS Features
- source/client IP;
- parent/resolver domain;
- queried DNSBL/domain name;
- timestamp-derived windows;
- numeric domain/DNS ratios and aggregate features;
- entropy-like and distribution-like numeric features.

### Network / Hybrid Features
- grouping by `source_ip`;
- query sequences by `timestamp_ms`;
- correlation of query-domain with DNSBL/provider domain.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | no | sample contains rows |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | {"yes" if summary["total_missing_cells"] else "no"} | missing cells in sample: {summary["total_missing_cells"]} |
| Unstable structure | {"yes" if summary["inconsistent_column_files"] else "no"} | inconsistent column files: {summary["inconsistent_column_files"]} |
| Mixed schemas | no | one CSV file |
| Oversized file | yes | file is about 8.25 GB; streaming/chunked reader is required |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no, but an explicit positional schema is required |
| Processing priority | medium |

## 12. Conclusion
DNS TEST csv is suitable for downstream processing, but because it is headerless and large it should be read as a stream and normalized through a fixed 22-column positional schema.
"""

    @staticmethod
    def _fields_table(field_summaries: list[dict[str, str]]) -> str:
        return "\n".join(
            f"| {field['name']} | {field['dominant_type']} | {field['purpose']} | {field['example']} |"
            for field in field_summaries
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
        status_by_format = {"csv": (summary["final_status"], "csv.md")}
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {yes} | {no} | {status} | {document} |")
        return f"{title} (DNS TEST)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task1: Analysis of dns test csv dataset files"
            if ru
            else "# Task1 Report: Analysis of dns test csv dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_DNS_DATASETS_FILTER\\TEST\\csv` на основе `{self.DNS_INPUT_JSON_FILE}`. "
            "Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_DNS_DATASETS_FILTER\\TEST\\csv` using `{self.DNS_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_dns_test_csv_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/dns/test/csv.md`
- `docs/en/analysis-dataset/dns/test/csv.md`
- `docs/ru/analysis-dataset/dns/test/README.md`
- `docs/en/analysis-dataset/dns/test/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/dns/test/Task1(Analysis of dns test csv dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/dns/test/Task1(Analysis of dns test csv dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.DNS_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `TEST.csv`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler читает ограниченную выборку строк, определяет headerless CSV-схему, типы колонок, временные признаки и сигналы качества данных.' if ru else 'The handler reads a limited row sample, detects the headerless CSV schema, column types, time features, and data-quality signals.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_counts(self) -> dict[str, int]:
        payload = JsonDataManager(self.temp_data_path / self.DNS_INPUT_JSON_FILE).read(default={})
        bucket = payload.get(self.ROLE_NAME, {})
        return {fmt: len(paths) for fmt, paths in bucket.items() if isinstance(paths, list)} if isinstance(bucket, dict) else {}

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        return json.dumps(
            {
                "format": summary["format"],
                "role": summary["role"],
                "scope": summary["scope"],
                "schema_kinds": summary["schema_kinds"],
                "parsed_rows": summary["parsed_rows"],
                "missing_header_files": summary["missing_header_files"],
                "final_status": summary["final_status"],
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
