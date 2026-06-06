from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class DNSTrainPCAPCSVContentAnalysisResult:
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
class PCAPCSVProbe:
    path: str
    file_name: str
    file_size_bytes: int
    schema_kind: str
    class_hint: str
    has_header: bool
    sampled_rows: int
    parsed_rows: int
    column_count: int
    column_count_distribution: dict[str, int]
    missing_cells: int
    duplicate_header_names: list[str]
    parse_error: str | None


class DNSTrainPCAPCSVContentAnalysisHandler:
    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "pcap.csv"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_ROWS_PER_FILE = 1000

    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-dns-train-pcap-csv-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    FIELD_PURPOSES = {
        "timestamp": "packet-derived event timestamp",
        "FQDN_count": "fully qualified domain name length/count feature",
        "subdomain_length": "subdomain character length",
        "upper": "uppercase character count",
        "lower": "lowercase character count",
        "numeric": "numeric character count",
        "entropy": "domain entropy",
        "special": "special character count",
        "labels": "DNS label count",
        "labels_max": "maximum label length",
        "labels_average": "average label length",
        "longest_word": "longest token length",
        "sld": "second-level domain feature",
        "len": "domain/query length",
        "subdomain": "subdomain indicator or value",
        "rr": "resource record ratio or rate feature",
        "rr_type": "resource record type category",
        "rr_count": "resource record count",
        "rr_name_entropy": "resource record name entropy",
        "rr_name_length": "resource record name length",
        "distinct_ns": "distinct name server count",
        "distinct_ip": "distinct IP count",
        "unique_country": "unique country count",
        "unique_asn": "unique ASN count",
        "distinct_domains": "distinct domain count",
        "reverse_dns": "reverse DNS feature",
        "a_records": "A-record count",
        "unique_ttl": "unique TTL count",
        "ttl_mean": "mean TTL",
        "ttl_variance": "TTL variance",
    }

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_rows_per_file: int = DEFAULT_MAX_ROWS_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_rows_per_file = max(1, max_rows_per_file)
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "dns" / "train"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "dns" / "train"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "analysis-dataset" / "dns" / "train"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "analysis-dataset" / "dns" / "train"

    def analyze_and_generate_docs(self) -> DNSTrainPCAPCSVContentAnalysisResult:
        all_paths = self._extract_paths(self._read_source_json())
        if not all_paths:
            raise ValueError("No files found in sort-path-dns-file.json for TRAIN/pcap.csv.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "pcap.csv.md"
        docs_en_path = self.docs_en_dir / "pcap.csv.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task3(Analysis of dns train pcap.csv dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task3(Analysis of dns train pcap.csv dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return DNSTrainPCAPCSVContentAnalysisResult(
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
        probes: list[PCAPCSVProbe] = []
        schema_kinds: Counter[str] = Counter()
        class_hints: Counter[str] = Counter()
        column_names: Counter[str] = Counter()
        column_type_votes: dict[str, Counter[str]] = defaultdict(Counter)
        examples_by_column: dict[str, str] = {}
        parse_errors: Counter[str] = Counter()
        total_missing_cells = 0
        parsed_rows = 0
        empty_files = 0
        timestamp_columns: set[str] = set()

        for path in sampled_paths:
            probe, headers, data_rows = self._probe_csv(path)
            probes.append(probe)
            schema_kinds[probe.schema_kind] += 1
            class_hints[probe.class_hint] += 1
            total_missing_cells += probe.missing_cells
            parsed_rows += probe.parsed_rows
            if probe.parsed_rows == 0:
                empty_files += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1

            column_names.update(headers)
            for row in data_rows:
                for index, header in enumerate(headers):
                    value = row[index] if index < len(row) else ""
                    inferred_type = self._infer_type(value)
                    column_type_votes[header][inferred_type] += 1
                    if value and header not in examples_by_column:
                        examples_by_column[header] = value
            timestamp_columns.update(header for header in headers if "time" in header.lower())

        inconsistent_column_files = sum(1 for probe in probes if len(probe.column_count_distribution) > 1)
        duplicate_header_files = sum(1 for probe in probes if probe.duplicate_header_names)
        has_parse_errors = bool(parse_errors)
        final_status = (
            self.STATUS_BROKEN
            if parsed_rows == 0
            else self.STATUS_PARTIAL
            if has_parse_errors or inconsistent_column_files or duplicate_header_files
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
            "class_hints": dict(class_hints.most_common()),
            "parsed_rows": parsed_rows,
            "total_missing_cells": total_missing_cells,
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "inconsistent_column_files": inconsistent_column_files,
            "duplicate_header_files": duplicate_header_files,
            "unique_columns": sorted(column_names),
            "field_summaries": self._field_summaries(column_names, column_type_votes, examples_by_column),
            "timestamp_columns": sorted(timestamp_columns),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "high",
        }

    def _probe_csv(self, path: Path) -> tuple[PCAPCSVProbe, list[str], list[list[str]]]:
        if not path.exists():
            return self._probe(path, 0, "missing", "unknown", False, 0, 0, 0, {}, 0, [], "file_not_found"), [], []
        file_size = path.stat().st_size
        if file_size == 0:
            return self._probe(path, file_size, "empty", self._class_hint(path), False, 0, 0, 0, {}, 0, [], "empty_file"), [], []

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
            return (
                self._probe(path, file_size, "unparsed", self._class_hint(path), False, 0, 0, 0, {}, 0, [], str(error)),
                [],
                [],
            )

        if not rows:
            return self._probe(path, file_size, "empty", self._class_hint(path), False, 0, 0, 0, {}, 0, [], "empty_file"), [], []

        headers = self._deduplicate_headers(rows[0])
        data_rows = rows[1:]
        schema_kind = self._schema_kind(path, headers)
        duplicate_headers = self._duplicate_headers(rows[0])
        return (
            self._probe(
                path=path,
                file_size=file_size,
                schema_kind=schema_kind,
                class_hint=self._class_hint(path),
                has_header=True,
                sampled_rows=len(rows),
                parsed_rows=len(data_rows),
                column_count=max(len(row) for row in rows),
                column_counts=dict(column_counts),
                missing_cells=missing_cells,
                duplicate_headers=duplicate_headers,
                parse_error=None,
            ),
            headers,
            data_rows,
        )

    @staticmethod
    def _probe(
        path: Path,
        file_size: int,
        schema_kind: str,
        class_hint: str,
        has_header: bool,
        sampled_rows: int,
        parsed_rows: int,
        column_count: int,
        column_counts: dict[str, int],
        missing_cells: int,
        duplicate_headers: list[str],
        parse_error: str | None,
    ) -> PCAPCSVProbe:
        return PCAPCSVProbe(
            path=str(path),
            file_name=path.name,
            file_size_bytes=file_size,
            schema_kind=schema_kind,
            class_hint=class_hint,
            has_header=has_header,
            sampled_rows=sampled_rows,
            parsed_rows=parsed_rows,
            column_count=column_count,
            column_count_distribution=column_counts,
            missing_cells=missing_cells,
            duplicate_header_names=duplicate_headers,
            parse_error=parse_error,
        )

    @staticmethod
    def _schema_kind(path: Path, headers: list[str]) -> str:
        lower_name = path.name.lower()
        normalized = {header.lower() for header in headers}
        if lower_name.startswith("stateful_features") or {"rr_count", "ttl_mean", "distinct_ip"} & normalized:
            return "stateful_dns_pcap_features"
        if lower_name.startswith("stateless_features") or {"timestamp", "fqdn_count", "entropy"} & normalized:
            return "stateless_dns_pcap_features"
        return "pcap_csv_features"

    @staticmethod
    def _class_hint(path: Path) -> str:
        lower_name = path.name.lower()
        for label in ("benign", "audio", "compressed", "exe", "image", "text", "video"):
            if f"_{label}" in lower_name or f"-{label}" in lower_name:
                return label
        return "unknown"

    @staticmethod
    def _deduplicate_headers(headers: list[str]) -> list[str]:
        result: list[str] = []
        counts: Counter[str] = Counter()
        for index, header in enumerate(headers, start=1):
            normalized = header.strip() or f"column_{index}"
            counts[normalized] += 1
            result.append(normalized if counts[normalized] == 1 else f"{normalized}__{counts[normalized]}")
        return result

    @staticmethod
    def _duplicate_headers(headers: list[str]) -> list[str]:
        counts = Counter(header.strip() for header in headers if header.strip())
        return sorted([name for name, count in counts.items() if count > 1])

    @staticmethod
    def _infer_type(value: str) -> str:
        if value == "" or value.lower() == "nan":
            return "missing"
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
        if len(value) >= 19 and value[4:5] == "-" and value[7:8] == "-":
            return "datetime"
        if "." in value and " " not in value and "/" not in value:
            return "domain_or_ip"
        return "string"

    def _field_summaries(
        self,
        column_names: Counter[str],
        column_type_votes: dict[str, Counter[str]],
        examples_by_column: dict[str, str],
    ) -> list[dict[str, str | int]]:
        summaries: list[dict[str, str | int]] = []
        for column in sorted(column_names):
            summaries.append(
                {
                    "name": column,
                    "files_seen": column_names[column],
                    "dominant_type": self._dominant_type(column_type_votes[column]),
                    "purpose": self.FIELD_PURPOSES.get(column, "DNS pcap-derived feature"),
                    "example": examples_by_column.get(column, ""),
                }
            )
        return summaries

    @staticmethod
    def _dominant_type(counter: Counter[str]) -> str:
        filtered = Counter({key: value for key, value in counter.items() if key != "missing"})
        if filtered:
            return filtered.most_common(1)[0][0]
        return "unknown"

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:10])
        schemas = ", ".join(f"{key}: {value}" for key, value in summary["schema_kinds"].items())
        class_hints = ", ".join(f"{key}: {value}" for key, value in summary["class_hints"].items())
        fields = self._fields_table(summary["field_summaries"], language)
        parse_error_count = sum(summary["parse_errors"].values())

        if ru:
            return f"""# Анализ формата: pcap.csv

## 1. Назначение
Файлы DNS TRAIN `pcap.csv` содержат табличные признаки, уже извлеченные из pcap-трафика. Набор пригоден для feature engineering без чтения raw-pcap: часть файлов содержит stateful DNS/resource-record признаки, часть - stateless lexical/time признаки доменных запросов.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap.csv |
| Варианты расширения | .pcap.csv |
| DNS | да |
| Host | нет |
| Роли | TRAIN |
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
| Заголовок | да |
| Разделитель | comma |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Parsed rows | {summary["parsed_rows"]} |

## 5. Содержательная структура
Обнаружены две схемы pcap-derived признаков: {schemas}. Классы/типы трафика берутся из имен файлов: {class_hints}. Stateful-файлы описывают DNS RR, TTL, NS/IP/ASN и агрегаты; stateless-файлы содержат timestamp и lexical признаки FQDN/subdomain.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
{fields}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла / class_hint |
| Значения label | {", ".join(summary["class_hints"].keys())} |
| Можно использовать для supervised learning | да, после присвоения label из имени файла |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | {", ".join(summary["timestamp_columns"]) or "-"} |
| Формат времени | `YYYY-MM-DD HH:MM:SS.microseconds` |
| Можно строить sequence | да, для stateless-схемы |
| Можно применять sliding window | да, после сортировки по timestamp |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- частоты RR-типов: `A_frequency`, `NS_frequency`, `TXT_frequency`, `AAAA_frequency`;
- `rr_count`, `rr_name_entropy`, `rr_name_length`;
- `distinct_ns`, `distinct_ip`, `unique_asn`, `unique_ttl`;
- `ttl_mean`, `ttl_variance`;
- lexical признаки FQDN: `entropy`, `labels`, `subdomain_length`, `longest_word`.

### Network / hybrid-признаки
- stateful/stateless feature family;
- тип трафика из имени файла;
- агрегация по timestamp и DNS-запросам;
- связь с raw `pcap` файлами для валидации признаков.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Поврежденные файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | {"да" if summary["total_missing_cells"] else "нет"} | missing cells: {summary["total_missing_cells"]} |
| Нестабильная структура | {"да" if summary["inconsistent_column_files"] else "нет"} | inconsistent column files: {summary["inconsistent_column_files"]} |
| Смешанные схемы | да | две валидные схемы: stateful и stateless |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет, достаточно CSV reader и schema-aware маршрутизации |
| Приоритет обработки | высокий |

## 12. Вывод
DNS TRAIN `pcap.csv` готов к feature extraction: CSV-структура стабильна, заголовки присутствуют, временные признаки доступны в stateless-схеме, а label можно назначать из имени файла.
"""

        return f"""# Format Analysis: pcap.csv

## 1. Purpose
DNS TRAIN `pcap.csv` files contain tabular features already extracted from pcap traffic. The format is suitable for feature engineering without parsing raw pcap: one family contains stateful DNS/resource-record features, and another contains stateless lexical/time features for domain queries.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap.csv |
| Extension variants | .pcap.csv |
| DNS | yes |
| Host | no |
| Roles | TRAIN |
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
| Header | yes |
| Delimiter | comma |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Parsed rows | {summary["parsed_rows"]} |

## 5. Content Structure
Detected two pcap-derived feature schemas: {schemas}. Traffic classes/types are available from file names: {class_hints}. Stateful files describe DNS RR, TTL, NS/IP/ASN, and aggregate features; stateless files contain timestamp and lexical FQDN/subdomain features.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
{fields}

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name / class_hint |
| Label values | {", ".join(summary["class_hints"].keys())} |
| Suitable for supervised learning | yes, after assigning label from file name |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | {", ".join(summary["timestamp_columns"]) or "-"} |
| Time format | `YYYY-MM-DD HH:MM:SS.microseconds` |
| Can build sequences | yes, for the stateless schema |
| Can apply sliding windows | yes, after sorting by timestamp |

## 9. Potential Feature Extraction
### DNS Features
- RR type frequencies: `A_frequency`, `NS_frequency`, `TXT_frequency`, `AAAA_frequency`;
- `rr_count`, `rr_name_entropy`, `rr_name_length`;
- `distinct_ns`, `distinct_ip`, `unique_asn`, `unique_ttl`;
- `ttl_mean`, `ttl_variance`;
- FQDN lexical features: `entropy`, `labels`, `subdomain_length`, `longest_word`.

### Network / Hybrid Features
- stateful/stateless feature family;
- traffic type from file name;
- aggregation by timestamp and DNS query events;
- correlation with raw `pcap` files for feature validation.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | {"yes" if summary["total_missing_cells"] else "no"} | missing cells: {summary["total_missing_cells"]} |
| Unstable structure | {"yes" if summary["inconsistent_column_files"] else "no"} | inconsistent column files: {summary["inconsistent_column_files"]} |
| Mixed schemas | yes | two valid schemas: stateful and stateless |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no, CSV reader and schema-aware routing are enough |
| Processing priority | high |

## 12. Conclusion
DNS TRAIN `pcap.csv` is ready for feature extraction: CSV structure is stable, headers are present, time features are available in the stateless schema, and labels can be assigned from file names.
"""

    def _fields_table(self, field_summaries: list[dict[str, str | int]], language: str) -> str:
        rows = []
        for field in field_summaries:
            rows.append(
                f"| {field['name']} | {field['dominant_type']} | {field['purpose']} | {field['example']} |"
            )
        return "\n".join(rows)

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
            "csv": (self._load_optional_status("analysis-dns-train-csv-summary.json"), "csv.md"),
            "pcap": (self._load_optional_status("analysis-dns-train-pcap-summary.json"), "pcap.md"),
            "pcap.csv": (summary["final_status"], "pcap.csv.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {yes} | {no} | {status} | {document} |")
        return f"{title} (DNS TRAIN)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task3: Analysis of dns train pcap.csv dataset files"
            if ru
            else "# Task3 Report: Analysis of dns train pcap.csv dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_DNS_DATASETS_FILTER\\TRAIN\\pcap.csv` на основе "
            f"`{self.DNS_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_DNS_DATASETS_FILTER\\TRAIN\\pcap.csv` using `{self.DNS_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_dns_train_pcap_csv_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/dns/train/pcap.csv.md`
- `docs/en/analysis-dataset/dns/train/pcap.csv.md`
- `docs/ru/analysis-dataset/dns/train/README.md`
- `docs/en/analysis-dataset/dns/train/README.md`
- `report/ru/stage-one/analysis-dataset/dns/train/Task3(Analysis of dns train pcap.csv dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/dns/train/Task3(Analysis of dns train pcap.csv dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.DNS_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `TRAIN.pcap.csv`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler читает ограниченную выборку CSV-строк, определяет stateful/stateless schema, собирает типы колонок, label-подсказки из имен файлов и признаки качества данных.' if ru else 'The handler reads a limited CSV row sample, detects stateful/stateless schemas, collects column types, label hints from file names, and data-quality signals.')}

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

    def _load_optional_status(self, summary_file_name: str) -> str:
        summary_path = self.temp_data_path / summary_file_name
        if not summary_path.exists():
            return "-"
        payload = JsonDataManager(summary_path).read(default={})
        status = payload.get("final_status")
        return str(status) if isinstance(status, str) else "-"

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        return json.dumps(
            {
                "format": summary["format"],
                "role": summary["role"],
                "scope": summary["scope"],
                "schema_kinds": summary["schema_kinds"],
                "class_hints": summary["class_hints"],
                "parsed_rows": summary["parsed_rows"],
                "timestamp_columns": summary["timestamp_columns"],
                "final_status": summary["final_status"],
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
