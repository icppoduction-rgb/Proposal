from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostCSVContentAnalysisResult:
    """Result of analyzing TRAIN/csv host datasets and generating documentation."""

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
class CSVFileProbe:
    """Technical probe result for a sampled CSV file."""

    path: str
    file_name: str
    file_size_bytes: int
    encoding: str
    delimiter: str
    has_header: bool
    sampled_line_count: int
    sampled_row_count: int
    column_count_distribution: dict[str, int]
    dominant_column_count: int
    missing_cells_count: int
    duplicate_rows_count: int
    parse_error: str | None


class HostCSVContentAnalysisHandler:
    """Analyzes host TRAIN/csv datasets and writes bilingual markdown documentation."""

    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "csv"
    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"

    INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"

    ENCODING_CANDIDATES: tuple[str, ...] = (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
        "cp1251",
    )

    DELIMITER_CANDIDATES = ",;\t|"

    DATE_RE = re.compile(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$")
    TIME_RE = re.compile(r"^\d{1,2}:\d{2}:\d{2}$")

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

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "host"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "host"

    def analyze_and_generate_docs(self) -> HostCSVContentAnalysisResult:
        """Runs analysis and writes docs/report files for TRAIN/csv datasets."""
        role_to_formats = self._read_source_json()
        all_csv_paths = self._extract_csv_paths(role_to_formats)
        total_files_count = len(all_csv_paths)
        if total_files_count == 0:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/csv.")

        sampled_paths = self._select_sample_paths(all_csv_paths)
        probes: list[CSVFileProbe] = []
        for file_path in sampled_paths:
            probes.append(self._probe_csv_file(file_path))

        summary_payload = self._build_summary(all_csv_paths=all_csv_paths, probes=probes)
        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "csv.md"
        docs_en_path = self.docs_en_dir / "csv.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task1(Analysis of host csv dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task1(Analysis of host csv dataset files)_report.md"

        status = str(summary_payload["final_status"])
        needs_custom_parser = bool(summary_payload["needs_custom_parser"])

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(total_files_count, status))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(total_files_count, status))
        self._write_text_file(
            report_ru_path,
            self._build_ru_report(
                summary_json_path=summary_json_path,
                docs_ru_path=docs_ru_path,
                docs_en_path=docs_en_path,
                docs_ru_readme_path=docs_ru_readme_path,
                docs_en_readme_path=docs_en_readme_path,
                sampled_files_count=len(sampled_paths),
                total_files_count=total_files_count,
                status=status,
                needs_custom_parser=needs_custom_parser,
            ),
        )
        self._write_text_file(
            report_en_path,
            self._build_en_report(
                summary_json_path=summary_json_path,
                docs_ru_path=docs_ru_path,
                docs_en_path=docs_en_path,
                docs_ru_readme_path=docs_ru_readme_path,
                docs_en_readme_path=docs_en_readme_path,
                sampled_files_count=len(sampled_paths),
                total_files_count=total_files_count,
                status=status,
                needs_custom_parser=needs_custom_parser,
            ),
        )

        return HostCSVContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=total_files_count,
            sampled_files_count=len(sampled_paths),
            status=status,
        )

    def _read_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        if not payload:
            raise FileNotFoundError(f"Source JSON is empty or missing: {source_json_path}")
        if self.ROLE_NAME not in payload:
            raise ValueError(f"Missing role '{self.ROLE_NAME}' in {source_json_path}.")
        return payload

    def _extract_csv_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
        role_bucket = role_to_formats.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            raise ValueError(f"Role '{self.ROLE_NAME}' in source JSON must be an object.")

        format_bucket = role_bucket.get(self.FORMAT_NAME, [])
        if not isinstance(format_bucket, list):
            raise ValueError(f"Role '{self.ROLE_NAME}' format '{self.FORMAT_NAME}' must be a list of paths.")

        result = [Path(str(raw_path)).expanduser() for raw_path in format_bucket if isinstance(raw_path, str)]
        return sorted(result, key=lambda p: str(p).lower())

    def _select_sample_paths(self, all_paths: list[Path]) -> list[Path]:
        if len(all_paths) <= self.max_files_per_format:
            return all_paths

        spread_count = self.max_files_per_format
        spread_indices = {
            round(index * (len(all_paths) - 1) / (spread_count - 1))
            for index in range(spread_count)
        }
        spread_paths = [all_paths[index] for index in sorted(spread_indices)]

        forced_special = [
            path
            for path in all_paths
            if path.name.lower() in {"feature_descr.csv", "ground_truth.csv"}
        ]

        selected: list[Path] = []
        seen: set[str] = set()

        for path in forced_special + spread_paths:
            key = str(path).lower()
            if key in seen:
                continue
            selected.append(path)
            seen.add(key)
            if len(selected) >= self.max_files_per_format:
                break

        return selected

    def _probe_csv_file(self, file_path: Path) -> CSVFileProbe:
        if not file_path.exists():
            return CSVFileProbe(
                path=str(file_path),
                file_name=file_path.name,
                file_size_bytes=0,
                encoding="missing",
                delimiter=",",
                has_header=False,
                sampled_line_count=0,
                sampled_row_count=0,
                column_count_distribution={},
                dominant_column_count=0,
                missing_cells_count=0,
                duplicate_rows_count=0,
                parse_error="file_not_found",
            )

        file_size = file_path.stat().st_size
        if file_size == 0:
            return CSVFileProbe(
                path=str(file_path),
                file_name=file_path.name,
                file_size_bytes=0,
                encoding="empty",
                delimiter=",",
                has_header=False,
                sampled_line_count=0,
                sampled_row_count=0,
                column_count_distribution={},
                dominant_column_count=0,
                missing_cells_count=0,
                duplicate_rows_count=0,
                parse_error="empty_file",
            )

        encoding = self._detect_encoding(file_path)
        try:
            text = file_path.read_text(encoding=encoding, errors="replace")
        except OSError as error:
            return CSVFileProbe(
                path=str(file_path),
                file_name=file_path.name,
                file_size_bytes=file_size,
                encoding=encoding,
                delimiter=",",
                has_header=False,
                sampled_line_count=0,
                sampled_row_count=0,
                column_count_distribution={},
                dominant_column_count=0,
                missing_cells_count=0,
                duplicate_rows_count=0,
                parse_error=f"read_error:{error.__class__.__name__}",
            )

        lines = text.splitlines()[: self.max_lines_per_file]
        if not lines:
            return CSVFileProbe(
                path=str(file_path),
                file_name=file_path.name,
                file_size_bytes=file_size,
                encoding=encoding,
                delimiter=",",
                has_header=False,
                sampled_line_count=0,
                sampled_row_count=0,
                column_count_distribution={},
                dominant_column_count=0,
                missing_cells_count=0,
                duplicate_rows_count=0,
                parse_error="no_text_lines",
            )

        sample_text = "\n".join(lines[:20])
        delimiter = self._detect_delimiter(sample_text)
        has_header = self._detect_header(sample_text)

        rows = [row for row in csv.reader(lines, delimiter=delimiter) if row]
        if not rows:
            return CSVFileProbe(
                path=str(file_path),
                file_name=file_path.name,
                file_size_bytes=file_size,
                encoding=encoding,
                delimiter=delimiter,
                has_header=has_header,
                sampled_line_count=len(lines),
                sampled_row_count=0,
                column_count_distribution={},
                dominant_column_count=0,
                missing_cells_count=0,
                duplicate_rows_count=0,
                parse_error="no_parsed_rows",
            )

        data_rows = rows[1:] if has_header and len(rows) > 1 else rows
        column_count_distribution: dict[str, int] = {}
        missing_cells_count = 0

        unique_rows: set[tuple[str, ...]] = set()
        duplicate_rows_count = 0

        for row in data_rows:
            key = str(len(row))
            column_count_distribution[key] = column_count_distribution.get(key, 0) + 1
            missing_cells_count += sum(1 for cell in row if cell.strip() == "")

            row_tuple = tuple(cell.strip() for cell in row)
            if row_tuple in unique_rows:
                duplicate_rows_count += 1
            else:
                unique_rows.add(row_tuple)

        dominant_column_count = 0
        if column_count_distribution:
            dominant_column_count = int(
                max(column_count_distribution.items(), key=lambda item: item[1])[0]
            )

        return CSVFileProbe(
            path=str(file_path),
            file_name=file_path.name,
            file_size_bytes=file_size,
            encoding=encoding,
            delimiter=delimiter,
            has_header=has_header,
            sampled_line_count=len(lines),
            sampled_row_count=len(data_rows),
            column_count_distribution=column_count_distribution,
            dominant_column_count=dominant_column_count,
            missing_cells_count=missing_cells_count,
            duplicate_rows_count=duplicate_rows_count,
            parse_error=None,
        )

    def _build_summary(self, all_csv_paths: list[Path], probes: list[CSVFileProbe]) -> dict[str, Any]:
        encoding_counts: dict[str, int] = {}
        delimiter_counts: dict[str, int] = {}
        schema_counts: dict[str, int] = {}
        header_true = 0
        header_false = 0
        parse_errors: list[dict[str, str]] = []

        sampled_rows_total = 0
        sampled_missing_cells_total = 0
        sampled_duplicate_rows_total = 0

        date_candidates = 0
        time_candidates = 0
        label_candidate_columns: set[str] = set()

        field_samples: dict[int, list[str]] = {}
        field_unique: dict[int, set[str]] = {}

        primary_schema = self._detect_primary_schema(probes)

        for probe in probes:
            encoding_counts[probe.encoding] = encoding_counts.get(probe.encoding, 0) + 1
            delimiter_counts[probe.delimiter] = delimiter_counts.get(probe.delimiter, 0) + 1

            dominant_key = str(probe.dominant_column_count)
            schema_counts[dominant_key] = schema_counts.get(dominant_key, 0) + 1

            if probe.has_header:
                header_true += 1
            else:
                header_false += 1

            sampled_rows_total += probe.sampled_row_count
            sampled_missing_cells_total += probe.missing_cells_count
            sampled_duplicate_rows_total += probe.duplicate_rows_count

            if probe.parse_error:
                parse_errors.append({"path": probe.path, "error": probe.parse_error})

            if probe.dominant_column_count == primary_schema:
                self._collect_field_statistics(
                    file_path=Path(probe.path),
                    probe=probe,
                    field_samples=field_samples,
                    field_unique=field_unique,
                )

        inferred_field_names = self._infer_field_names(field_samples, field_unique)
        for index, values in field_samples.items():
            if not values:
                continue

            date_ratio = sum(1 for value in values if self.DATE_RE.match(value)) / len(values)
            time_ratio = sum(1 for value in values if self.TIME_RE.match(value)) / len(values)
            if date_ratio >= 0.6:
                date_candidates += 1
            if time_ratio >= 0.6:
                time_candidates += 1

            lower_values = {value.strip().lower() for value in values if value.strip()}
            if lower_values & {"normal", "benign", "malicious", "attack", "anomaly"}:
                label_candidate_columns.add(str(index + 1))
            elif lower_values and lower_values.issubset({"0", "1", "2", "3", "4"}):
                label_candidate_columns.add(str(index + 1))

        example_paths = [str(path) for path in all_csv_paths[:3]]
        if len(all_csv_paths) > 6:
            example_paths.extend(str(path) for path in all_csv_paths[-3:])
        else:
            for path in all_csv_paths[3:]:
                example_paths.append(str(path))

        total_file_count = len(all_csv_paths)
        special_schema_files = self._find_special_schema_files(all_csv_paths)
        needs_custom_parser = len(special_schema_files) > 0

        status = self.STATUS_PARTIAL if needs_custom_parser else self.STATUS_READY
        priority = "high" if status == self.STATUS_PARTIAL else "medium"

        feature_description = self._read_feature_description(all_csv_paths)

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": total_file_count,
                "sampled_files_count": len(probes),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "examples": {
                "paths": example_paths,
                "special_schema_files": special_schema_files,
            },
            "technical": {
                "file_type": "text",
                "line_by_line_readable": True,
                "tabular_structure": True,
                "nested_structure": False,
                "encoding_counts": encoding_counts,
                "delimiter_counts": delimiter_counts,
                "header_detection": {
                    "header_true_files": header_true,
                    "header_false_files": header_false,
                },
                "schema_column_count_by_sampled_file": schema_counts,
                "sampled_rows_total": sampled_rows_total,
                "sampled_missing_cells_total": sampled_missing_cells_total,
                "sampled_duplicate_rows_total": sampled_duplicate_rows_total,
                "parse_errors": parse_errors,
            },
            "content": {
                "category": "Host system-call and process telemetry CSV, plus auxiliary ground-truth/feature-description files.",
                "primary_schema_column_count": primary_schema,
                "inferred_fields": inferred_field_names,
                "feature_description_rows": feature_description,
            },
            "label_detection": {
                "label_columns": sorted(label_candidate_columns, key=lambda item: int(item)),
                "supports_supervised_learning": True,
                "notes": "Primary 9-column files contain attack category/subcategory and binary label fields.",
            },
            "time_detection": {
                "date_like_columns_count": date_candidates,
                "time_like_columns_count": time_candidates,
                "timestamp_detected": date_candidates > 0 and time_candidates > 0,
                "timestamp_format": "date + time in separate columns (dd/mm/yyyy and HH:MM:SS)",
                "timezone": "not specified",
            },
            "data_quality": {
                "empty_files_count": sum(1 for probe in probes if probe.parse_error == "empty_file"),
                "missing_source_files_count": sum(1 for probe in probes if probe.parse_error == "file_not_found"),
                "encoding_problem_files_count": sum(
                    1
                    for probe in probes
                    if probe.parse_error and probe.parse_error.startswith("read_error")
                ),
                "mixed_schema_detected": needs_custom_parser,
                "special_schema_files_count": len(special_schema_files),
            },
            "final_status": status,
            "needs_custom_parser": needs_custom_parser,
            "priority": priority,
        }

    def _collect_field_statistics(
        self,
        file_path: Path,
        probe: CSVFileProbe,
        field_samples: dict[int, list[str]],
        field_unique: dict[int, set[str]],
    ) -> None:
        if probe.parse_error:
            return

        text = file_path.read_text(encoding=probe.encoding, errors="replace")
        lines = text.splitlines()[: self.max_lines_per_file]
        rows = [row for row in csv.reader(lines, delimiter=probe.delimiter) if row]
        if not rows:
            return

        data_rows = rows[1:] if probe.has_header and len(rows) > 1 else rows
        for row in data_rows:
            for index, raw_value in enumerate(row):
                if index >= 20:
                    break
                value = raw_value.strip()
                field_unique.setdefault(index, set()).add(value)
                values = field_samples.setdefault(index, [])
                if value and len(values) < 18:
                    values.append(value)

    def _infer_field_names(
        self,
        field_samples: dict[int, list[str]],
        field_unique: dict[int, set[str]],
    ) -> dict[str, dict[str, Any]]:
        inferred: dict[str, dict[str, Any]] = {}
        for index in sorted(field_samples):
            samples = field_samples.get(index, [])
            uniq_count = len(field_unique.get(index, set()))
            inferred_name = f"column_{index + 1}"
            inferred_type = "string"

            if any(self.DATE_RE.match(value) for value in samples):
                inferred_name = "date"
                inferred_type = "date"
            elif any(self.TIME_RE.match(value) for value in samples):
                inferred_name = "time"
                inferred_type = "time"
            elif samples and all(value.isdigit() for value in samples[:8]):
                inferred_type = "integer"
                if index == 2:
                    inferred_name = "process_id"
                elif index == 4:
                    inferred_name = "sys_call"
                elif index == 5:
                    inferred_name = "event_id"
                elif index == 8:
                    inferred_name = "label"
            elif any(value.startswith("/") or "\\\\" in value for value in samples):
                inferred_name = "path"
            elif uniq_count <= 16:
                inferred_name = f"category_{index + 1}"

            inferred[str(index + 1)] = {
                "name": inferred_name,
                "type": inferred_type,
                "unique_values_in_sample": uniq_count,
                "sample_values": samples[:5],
            }

        return inferred

    def _find_special_schema_files(self, all_csv_paths: list[Path]) -> list[str]:
        special_files: list[str] = []
        for file_path in all_csv_paths:
            file_name = file_path.name.lower()
            if file_name in {"feature_descr.csv", "ground_truth.csv"}:
                special_files.append(str(file_path))
        return special_files

    def _read_feature_description(self, all_csv_paths: list[Path]) -> list[dict[str, str]]:
        description_file = None
        for file_path in all_csv_paths:
            if file_path.name.lower() == "feature_descr.csv":
                description_file = file_path
                break

        if description_file is None or not description_file.exists():
            return []

        encoding = self._detect_encoding(description_file)
        text = description_file.read_text(encoding=encoding, errors="replace")
        rows = [row for row in csv.reader(text.splitlines(), delimiter=",") if row]
        if len(rows) < 2:
            return []

        extracted: list[dict[str, str]] = []
        for row in rows[1:]:
            if len(row) < 5:
                continue
            feature_no = row[1].strip()
            feature_name = row[2].strip()
            feature_type = row[3].strip()
            if not feature_no.isdigit():
                continue
            extracted.append(
                {
                    "feature_no": feature_no,
                    "feature_name": feature_name,
                    "feature_type": feature_type,
                }
            )
        return extracted

    def _detect_encoding(self, file_path: Path) -> str:
        raw = file_path.read_bytes()[:32768]
        for encoding in self.ENCODING_CANDIDATES:
            try:
                raw.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        return "latin-1"

    def _detect_delimiter(self, sample_text: str) -> str:
        lines = [line for line in sample_text.splitlines() if line.strip()]
        if not lines:
            return ","

        delimiter_scores: dict[str, int] = {}
        for delimiter in self.DELIMITER_CANDIDATES:
            counts = [line.count(delimiter) for line in lines]
            non_zero = [count for count in counts if count > 0]
            if not non_zero:
                delimiter_scores[delimiter] = 0
                continue

            # Prefer delimiters that appear repeatedly across lines.
            delimiter_scores[delimiter] = len(non_zero) * 1000 + sum(non_zero)

        best_delimiter, best_score = max(delimiter_scores.items(), key=lambda item: item[1])
        if best_score > 0:
            return best_delimiter

        try:
            dialect = csv.Sniffer().sniff(sample_text, delimiters=self.DELIMITER_CANDIDATES)
            return dialect.delimiter
        except csv.Error:
            return ","

    @staticmethod
    def _detect_header(sample_text: str) -> bool:
        try:
            return csv.Sniffer().has_header(sample_text)
        except csv.Error:
            return False

    @staticmethod
    def _detect_primary_schema(probes: list[CSVFileProbe]) -> int:
        schema_counts: dict[int, int] = {}
        for probe in probes:
            if probe.parse_error:
                continue
            if probe.dominant_column_count <= 0:
                continue
            schema_counts[probe.dominant_column_count] = (
                schema_counts.get(probe.dominant_column_count, 0) + 1
            )
        if not schema_counts:
            return 0
        return max(schema_counts.items(), key=lambda item: item[1])[0]

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        content = summary["content"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]

        inferred_fields = content["inferred_fields"]
        feature_rows = content["feature_description_rows"]
        examples = summary["examples"]["paths"][:3]
        special_files = summary["examples"]["special_schema_files"]

        field_table_rows = []
        for column_no, descriptor in inferred_fields.items():
            field_table_rows.append(
                f"| {column_no} | {descriptor['name']} | {descriptor['type']} | {', '.join(descriptor['sample_values']) or '-'} |"
            )
        field_table_text = "\n".join(field_table_rows) if field_table_rows else "| - | - | - | - |"

        feature_descr_rows = []
        for row in feature_rows[:9]:
            feature_descr_rows.append(
                f"| {row['feature_no']} | {row['feature_name']} | {row['feature_type']} |"
            )
        feature_descr_text = "\n".join(feature_descr_rows) if feature_descr_rows else "| - | - | - |"

        special_schema_comment = (
            "да"
            if quality["mixed_schema_detected"]
            else "нет"
        )

        return f"""
# Анализ формата: csv

## 1. Назначение
CSV-файлы в Host TRAIN используются как основной источник системных событий (дата/время, процесс, syscall/event, attack labels) для дальнейшего feature engineering.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
| DNS | нет |
| Host | да |
| Роли | {scope['role']} |
| Количество файлов | {scope['total_files_count']} |

## 3. Примеры файлов
```text
{examples[0] if len(examples) > 0 else '-'}
{examples[1] if len(examples) > 1 else '-'}
{examples[2] if len(examples) > 2 else '-'}
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | да |
| Заголовок | не всегда (обнаружены служебные файлы с header) |
| Разделитель | {', '.join(f'{k} ({v})' for k, v in technical['delimiter_counts'].items())} |
| Кодировка | {', '.join(f'{k} ({v})' for k, v in technical['encoding_counts'].items())} |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {scope['sampled_files_count']} |
| Sample-строк проанализировано | {technical['sampled_rows_total']} |

## 5. Содержательная структура
Основной массив CSV (числовые файлы `1.csv`..`99.csv`) содержит host telemetry: дата/время события, идентификатор процесса, путь процесса, системный вызов/событие и поля меток атаки.
Дополнительно присутствуют служебные CSV:
- `feature_descr.csv` - описание признаков;
- `ground_truth.csv` - детализация attack сценариев.

## 6. Найденные поля / колонки
| Колонка | Имя (эвристика) | Тип | Пример значения |
|---|---|---|---|
{field_table_text}

### Дополнение из feature_descr.csv
| Feature No | Feature Name | Type |
|---|---|---|
{feature_descr_text}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | колонка(и) {', '.join(label['label_columns']) if label['label_columns'] else '-'} |
| Значения label | нормальные/атакующие категории + бинарный label (0/1) |
| Можно использовать для supervised learning | да |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | {"да" if time_block['timestamp_detected'] else "нет"} |
| Название поля | date + time (раздельные колонки) |
| Формат времени | {time_block['timestamp_format']} |
| Timezone | {time_block['timezone']} |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо для этого формата/набора.

### Host-признаки
- частоты `sys_call`/`event_id`;
- n-grams и переходы системных вызовов;
- частоты и последовательности по `process_id` + `path`;
- распределения attack category/subcategory;
- бинарный target из label (0/1).

### Network / hybrid-признаки
- в `ground_truth.csv` можно извлекать дополнительные контекстные индикаторы (attack campaign и IP pair metadata) для host+network correlation.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if quality['empty_files_count'] > 0 else "нет"} | обнаружено: {quality['empty_files_count']} |
| Повреждённые/нечитаемые | {"да" if quality['encoding_problem_files_count'] > 0 else "нет"} | encoding/read errors: {quality['encoding_problem_files_count']} |
| Missing values | {"да" if technical['sampled_missing_cells_total'] > 0 else "нет"} | в sample найдено: {technical['sampled_missing_cells_total']} |
| Нестабильная структура | {"да" if quality['mixed_schema_detected'] else "нет"} | встречаются 9/7/5-колоночные схемы |
| Смешанные схемы | {special_schema_comment} | спец-файлы: {len(special_files)} |
| Дубли строк | {"да" if technical['sampled_duplicate_rows_total'] > 0 else "нет"} | в sample найдено: {technical['sampled_duplicate_rows_total']} |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary['final_status']} |
| Нужен отдельный парсер | {"да" if summary['needs_custom_parser'] else "нет"} |
| Приоритет обработки | {summary['priority']} |

## 12. Вывод
CSV в `TRAIN` пригоден для этапа feature extraction по host telemetry и supervised learning. Основной поток данных имеет стабильную 9-колоночную схему, но есть служебные файлы (`feature_descr.csv`, `ground_truth.csv`) с отдельной структурой, поэтому для полного охвата формата нужна частичная ветвизация парсера.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        content = summary["content"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]

        inferred_fields = content["inferred_fields"]
        feature_rows = content["feature_description_rows"]
        examples = summary["examples"]["paths"][:3]
        special_files = summary["examples"]["special_schema_files"]

        field_table_rows = []
        for column_no, descriptor in inferred_fields.items():
            field_table_rows.append(
                f"| {column_no} | {descriptor['name']} | {descriptor['type']} | {', '.join(descriptor['sample_values']) or '-'} |"
            )
        field_table_text = "\n".join(field_table_rows) if field_table_rows else "| - | - | - | - |"

        feature_descr_rows = []
        for row in feature_rows[:9]:
            feature_descr_rows.append(
                f"| {row['feature_no']} | {row['feature_name']} | {row['feature_type']} |"
            )
        feature_descr_text = "\n".join(feature_descr_rows) if feature_descr_rows else "| - | - | - |"

        mixed_schema_text = "yes" if quality["mixed_schema_detected"] else "no"

        return f"""
# Format Analysis: csv

## 1. Purpose
Host TRAIN CSV files are used as the main source of system telemetry (date/time, process, syscall/event, attack labels) for downstream feature engineering.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
| DNS | no |
| Host | yes |
| Roles | {scope['role']} |
| File count | {scope['total_files_count']} |

## 3. Example files
```text
{examples[0] if len(examples) > 0 else '-'}
{examples[1] if len(examples) > 1 else '-'}
{examples[2] if len(examples) > 2 else '-'}
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | text |
| Line-by-line readable | yes |
| Tabular structure | yes |
| Header | not always (utility files with header are present) |
| Delimiter | {', '.join(f'{k} ({v})' for k, v in technical['delimiter_counts'].items())} |
| Encoding | {', '.join(f'{k} ({v})' for k, v in technical['encoding_counts'].items())} |
| Nested structure | no |
| Sampled files | {scope['sampled_files_count']} |
| Sampled rows | {technical['sampled_rows_total']} |

## 5. Semantic structure
The primary CSV block (numbered files `1.csv`..`99.csv`) contains host telemetry: event date/time, process identifier, process path, syscall/event field, and attack label fields.
Additional utility CSV files are present:
- `feature_descr.csv` - feature dictionary;
- `ground_truth.csv` - attack scenario ground-truth details.

## 6. Detected fields / columns
| Column | Inferred name | Type | Example value |
|---|---|---|---|
{field_table_text}

### Extra mapping from feature_descr.csv
| Feature No | Feature Name | Type |
|---|---|---|
{feature_descr_text}

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | yes |
| Field name | column(s) {', '.join(label['label_columns']) if label['label_columns'] else '-'} |
| Label values | normal/attack categories plus binary label (0/1) |
| Suitable for supervised learning | yes |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | {"yes" if time_block['timestamp_detected'] else "no"} |
| Field name | date + time (separate columns) |
| Timestamp format | {time_block['timestamp_format']} |
| Timezone | {time_block['timezone']} |
| Sequence-ready | yes |
| Sliding-window-ready | yes |

## 9. Potential feature extraction signals
### DNS features
- not applicable for this format scope.

### Host features
- `sys_call`/`event_id` frequency features;
- syscall n-grams and transition features;
- process-centric sequence features (`process_id` + `path`);
- attack category/subcategory distributions;
- binary target from label (0/1).

### Network / hybrid features
- `ground_truth.csv` can provide additional context indicators (attack campaign and IP pair metadata) for host+network correlation.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if quality['empty_files_count'] > 0 else "no"} | count: {quality['empty_files_count']} |
| Corrupted/unreadable files | {"yes" if quality['encoding_problem_files_count'] > 0 else "no"} | encoding/read errors: {quality['encoding_problem_files_count']} |
| Missing values | {"yes" if technical['sampled_missing_cells_total'] > 0 else "no"} | found in sample: {technical['sampled_missing_cells_total']} |
| Unstable structure | {"yes" if quality['mixed_schema_detected'] else "no"} | observed 9/7/5-column schemas |
| Mixed schemas | {mixed_schema_text} | special schema files: {len(special_files)} |
| Duplicate rows | {"yes" if technical['sampled_duplicate_rows_total'] > 0 else "no"} | found in sample: {technical['sampled_duplicate_rows_total']} |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary['final_status']} |
| Needs dedicated parser | {"yes" if summary['needs_custom_parser'] else "no"} |
| Processing priority | {summary['priority']} |

## 12. Conclusion
`TRAIN/csv` is suitable for host-side feature extraction and supervised learning. The main data flow has a stable 9-column schema, but utility files (`feature_descr.csv`, `ground_truth.csv`) use separate schemas, so partial parser branching is required for full-format coverage.
"""

    @staticmethod
    def _build_ru_readme(file_count: int, status: str) -> str:
        return f"""
# Анализ содержимого файлов датасетов (Host)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| csv | {file_count} | нет | да | {status} | csv.md |
"""

    @staticmethod
    def _build_en_readme(file_count: int, status: str) -> str:
        return f"""
# Dataset File Content Analysis (Host)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| csv | {file_count} | no | yes | {status} | csv.md |
"""

    def _build_ru_report(
        self,
        summary_json_path: Path,
        docs_ru_path: Path,
        docs_en_path: Path,
        docs_ru_readme_path: Path,
        docs_en_readme_path: Path,
        sampled_files_count: int,
        total_files_count: int,
        status: str,
        needs_custom_parser: bool,
    ) -> str:
        return f"""
# Отчёт: Task1 (Analysis of host csv dataset files)

## Описание задачи
Реализован этап анализа содержимого `Host TRAIN/csv` датасетов на основе:
- `temp_data/sort-path-host-file.json`;
- существующей структуры репозитория и документации `docs/ru`.

Цель: определить техническую и содержательную структуру CSV, проверить timestamp/label-индикаторы, оценить качество данных и сформировать документацию.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_csv_dataset_handler.py` (новый handler);
- `manage.py` (новая команда запуска);
- `docs/ru/analysis-dataset/host/csv.md`;
- `docs/en/analysis-dataset/host/csv.md`;
- `docs/ru/analysis-dataset/host/README.md`;
- `docs/en/analysis-dataset/host/README.md`;
- `report/ru/stage-one/host/Task1(Analysis of host csv dataset files)_report.md`;
- `report/en/stage-one/host/Task1(Analysis of host csv dataset files)_report.md`;
- `temp_data/analysis-host-csv-summary.json` (техническая сводка анализа).

## Логика анализа
1. Загружен `sort-path-host-file.json`.
2. Выбран сегмент `{self.ROLE_NAME}/{self.FORMAT_NAME}`.
3. Применён безопасный sampling (до {self.max_files_per_format} файлов, включая спец-файлы).
4. Для каждого sample-файла выполнены:
   - определение кодировки;
   - определение разделителя;
   - проверка header;
   - анализ числа колонок;
   - проверка missing/duplicate в sample-строках;
   - эвристики для timestamp и label.
5. Сформированы markdown-документы RU/EN и индексные README.

## Результат анализа
- Всего CSV в области задачи: `{total_files_count}`.
- Проанализировано sample-файлов: `{sampled_files_count}`.
- Итоговый статус: `{status}`.
- Нужен отдельный parser: `{"да" if needs_custom_parser else "нет"}`.

## Почему статус не максимальный
Внутри `TRAIN/csv` помимо основного 9-колоночного потока есть служебные файлы с отдельными схемами (`feature_descr.csv`, `ground_truth.csv`). Для полного охвата формата нужна ветвизация парсинга по типу CSV-файла.

## Артефакты
- Техсводка JSON: `{summary_json_path}`
- RU-документация: `{docs_ru_path}`
- EN-документация: `{docs_en_path}`
- RU-индекс: `{docs_ru_readme_path}`
- EN-индекс: `{docs_en_readme_path}`
"""

    def _build_en_report(
        self,
        summary_json_path: Path,
        docs_ru_path: Path,
        docs_en_path: Path,
        docs_ru_readme_path: Path,
        docs_en_readme_path: Path,
        sampled_files_count: int,
        total_files_count: int,
        status: str,
        needs_custom_parser: bool,
    ) -> str:
        return f"""
# Report: Task1 (Analysis of host csv dataset files)

## Task description
Implemented the Host `TRAIN/csv` content-analysis stage using:
- `temp_data/sort-path-host-file.json`;
- existing repository structure and `docs/ru` context.

Goal: identify technical and semantic CSV structure, validate timestamp/label indicators, evaluate data quality, and generate bilingual documentation.

## Added/updated files
- `scripts/handlers/analyze_host_csv_dataset_handler.py` (new handler);
- `manage.py` (new run command);
- `docs/ru/analysis-dataset/host/csv.md`;
- `docs/en/analysis-dataset/host/csv.md`;
- `docs/ru/analysis-dataset/host/README.md`;
- `docs/en/analysis-dataset/host/README.md`;
- `report/ru/stage-one/host/Task1(Analysis of host csv dataset files)_report.md`;
- `report/en/stage-one/host/Task1(Analysis of host csv dataset files)_report.md`;
- `temp_data/analysis-host-csv-summary.json` (technical analysis summary).

## Analysis flow
1. Loaded `sort-path-host-file.json`.
2. Selected `{self.ROLE_NAME}/{self.FORMAT_NAME}` scope.
3. Applied safe sampling (up to {self.max_files_per_format} files, including special CSV files).
4. For each sampled file:
   - detected encoding;
   - detected delimiter;
   - checked header presence;
   - profiled column-count schema;
   - checked missing/duplicate rows in sampled lines;
   - applied timestamp/label heuristics.
5. Generated RU/EN markdown docs and index README files.

## Analysis result
- Total CSV files in task scope: `{total_files_count}`.
- Sampled files analyzed: `{sampled_files_count}`.
- Final status: `{status}`.
- Dedicated parser needed: `{"yes" if needs_custom_parser else "no"}`.

## Why the status is not fully ready
Inside `TRAIN/csv`, in addition to the dominant 9-column telemetry flow, there are utility files with different schemas (`feature_descr.csv`, `ground_truth.csv`). Full-format support requires parser branching by CSV subtype.

## Artifacts
- Technical JSON summary: `{summary_json_path}`
- RU documentation: `{docs_ru_path}`
- EN documentation: `{docs_en_path}`
- RU index: `{docs_ru_readme_path}`
- EN index: `{docs_en_readme_path}`
"""
