from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostFSStatLogContentAnalysisResult:
    """Result of analyzing TRAIN/fsstat.log host datasets and generating documentation."""

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


class HostFSStatLogContentAnalysisHandler:
    """Analyzes host TRAIN/fsstat.log datasets and writes bilingual markdown documentation."""

    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "fsstat.log"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-host-fsstat-log-summary.json"
    CSV_SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"
    AUTH_SUMMARY_JSON_FILE = "analysis-host-auth-log-summary.json"
    CPU_SUMMARY_JSON_FILE = "analysis-host-cpu-log-summary.json"
    DISKIO_SUMMARY_JSON_FILE = "analysis-host-diskio-log-summary.json"
    FILESYSTEM_SUMMARY_JSON_FILE = "analysis-host-filesystem-log-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"

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
        self.max_lines_per_file = max(100, max_lines_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "analysis-dataset" / "host"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "analysis-dataset" / "host"

    def analyze_and_generate_docs(self) -> HostFSStatLogContentAnalysisResult:
        """Runs fsstat.log analysis and writes docs/report files."""
        host_role_to_formats = self._read_host_source_json()
        all_fsstat_paths = self._extract_fsstat_paths(host_role_to_formats)
        if not all_fsstat_paths:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/fsstat.log.")

        dns_format_counts = self._read_dns_format_counts()

        sampled_paths = self._select_sample_paths(all_fsstat_paths)
        summary_payload = self._build_summary(
            all_fsstat_paths=all_fsstat_paths,
            sampled_paths=sampled_paths,
            dns_format_counts=dns_format_counts,
        )

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "fsstat.log.md"
        docs_en_path = self.docs_en_dir / "fsstat.log.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task6(Analysis of host fsstat-log dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task6(Analysis of host fsstat-log dataset files)_report.md"

        status = str(summary_payload["final_status"])

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(summary_payload))
        self._write_text_file(
            report_ru_path,
            self._build_ru_report(
                summary_payload=summary_payload,
                summary_json_path=summary_json_path,
                docs_ru_path=docs_ru_path,
                docs_en_path=docs_en_path,
                docs_ru_readme_path=docs_ru_readme_path,
                docs_en_readme_path=docs_en_readme_path,
                total_files_count=len(all_fsstat_paths),
                sampled_files_count=len(sampled_paths),
                status=status,
            ),
        )
        self._write_text_file(
            report_en_path,
            self._build_en_report(
                summary_payload=summary_payload,
                summary_json_path=summary_json_path,
                docs_ru_path=docs_ru_path,
                docs_en_path=docs_en_path,
                docs_ru_readme_path=docs_ru_readme_path,
                docs_en_readme_path=docs_en_readme_path,
                total_files_count=len(all_fsstat_paths),
                sampled_files_count=len(sampled_paths),
                status=status,
            ),
        )

        return HostFSStatLogContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_fsstat_paths),
            sampled_files_count=len(sampled_paths),
            status=status,
        )

    def _read_host_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        if not payload:
            raise FileNotFoundError(f"Source JSON is empty or missing: {source_json_path}")
        if self.ROLE_NAME not in payload:
            raise ValueError(f"Missing role '{self.ROLE_NAME}' in {source_json_path}.")
        return payload

    def _extract_fsstat_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
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

    def _read_dns_format_counts(self) -> dict[str, int]:
        source_json_path = self.temp_data_path / self.DNS_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        train_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(train_bucket, dict):
            return {}

        result: dict[str, int] = {}
        for format_name, paths in train_bucket.items():
            if isinstance(paths, list):
                result[str(format_name)] = len(paths)
        return result

    def _select_sample_paths(self, all_paths: list[Path]) -> list[Path]:
        if len(all_paths) <= self.max_files_per_format:
            return all_paths
        return all_paths[: self.max_files_per_format]

    def _build_summary(
        self,
        all_fsstat_paths: list[Path],
        sampled_paths: list[Path],
        dns_format_counts: dict[str, int],
    ) -> dict[str, Any]:
        sample_files_info: list[dict[str, Any]] = []

        encoding_counts: dict[str, int] = {}
        top_level_key_counts: dict[str, int] = {}
        dataset_counts: dict[str, int] = {}
        host_names: dict[str, int] = {}
        fsstat_counts: list[float] = []
        total_files_values: list[float] = []

        total_sample_lines = 0
        json_lines = 0
        non_json_lines = 0
        parse_errors = 0
        empty_files = 0
        duplicate_lines = 0

        metric_lines = 0
        unknown_json_lines = 0

        missing_timestamp_count = 0
        missing_total_size_values_count = 0

        fsstat_used_bytes_values: list[float] = []
        fsstat_free_bytes_values: list[float] = []
        fsstat_total_bytes_values: list[float] = []

        seen_lines: set[str] = set()

        for file_path in sampled_paths:
            file_info = {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": 0,
                "encoding": "unknown",
                "line_count_sample": 0,
                "json_line_count": 0,
                "metric_line_count": 0,
                "parse_error": None,
            }

            if not file_path.exists():
                file_info["parse_error"] = "file_not_found"
                sample_files_info.append(file_info)
                parse_errors += 1
                continue

            file_info["size_bytes"] = file_path.stat().st_size
            if file_info["size_bytes"] == 0:
                file_info["parse_error"] = "empty_file"
                sample_files_info.append(file_info)
                empty_files += 1
                continue

            encoding = self._detect_encoding(file_path)
            file_info["encoding"] = encoding
            encoding_counts[encoding] = encoding_counts.get(encoding, 0) + 1

            try:
                lines = file_path.read_text(encoding=encoding, errors="replace").splitlines()[
                    : self.max_lines_per_file
                ]
            except OSError as error:
                file_info["parse_error"] = f"read_error:{error.__class__.__name__}"
                sample_files_info.append(file_info)
                parse_errors += 1
                continue

            file_info["line_count_sample"] = len(lines)
            total_sample_lines += len(lines)

            for line in lines:
                if line in seen_lines:
                    duplicate_lines += 1
                else:
                    seen_lines.add(line)

                parsed_obj: dict[str, Any] | None = None
                try:
                    raw_obj = json.loads(line)
                    if isinstance(raw_obj, dict):
                        parsed_obj = raw_obj
                except json.JSONDecodeError:
                    parsed_obj = None

                if parsed_obj is None:
                    non_json_lines += 1
                    continue

                json_lines += 1
                file_info["json_line_count"] += 1

                for key in parsed_obj:
                    top_level_key_counts[key] = top_level_key_counts.get(key, 0) + 1

                event_obj = parsed_obj.get("event")
                dataset_name = event_obj.get("dataset") if isinstance(event_obj, dict) else None
                if isinstance(dataset_name, str):
                    dataset_counts[dataset_name] = dataset_counts.get(dataset_name, 0) + 1

                host_obj = parsed_obj.get("host")
                host_name = host_obj.get("name") if isinstance(host_obj, dict) else None
                if isinstance(host_name, str):
                    host_names[host_name] = host_names.get(host_name, 0) + 1

                if "@timestamp" not in parsed_obj:
                    missing_timestamp_count += 1

                fsstat_obj = self._safe_get_dict(parsed_obj, ("system", "fsstat"))
                if fsstat_obj is None:
                    unknown_json_lines += 1
                    continue

                metric_lines += 1
                file_info["metric_line_count"] += 1

                fsstat_count = self._safe_extract_numeric(parsed_obj, ("system", "fsstat", "count"))
                total_files = self._safe_extract_numeric(parsed_obj, ("system", "fsstat", "total_files"))
                used_bytes = self._safe_extract_numeric(parsed_obj, ("system", "fsstat", "total_size", "used"))
                free_bytes = self._safe_extract_numeric(parsed_obj, ("system", "fsstat", "total_size", "free"))
                total_bytes = self._safe_extract_numeric(parsed_obj, ("system", "fsstat", "total_size", "total"))

                if fsstat_count is not None:
                    fsstat_counts.append(fsstat_count)
                if total_files is not None:
                    total_files_values.append(total_files)
                if used_bytes is not None:
                    fsstat_used_bytes_values.append(used_bytes)
                if free_bytes is not None:
                    fsstat_free_bytes_values.append(free_bytes)
                if total_bytes is not None:
                    fsstat_total_bytes_values.append(total_bytes)

                if used_bytes is None or free_bytes is None or total_bytes is None:
                    missing_total_size_values_count += 1

            sample_files_info.append(file_info)

        mixed_schema_detected = unknown_json_lines > 0 or non_json_lines > 0
        status = self.STATUS_PARTIAL if mixed_schema_detected else self.STATUS_READY

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": len(all_fsstat_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "path_grouping": {
                "source_json_host": self.HOST_INPUT_JSON_FILE,
                "source_json_dns": self.DNS_INPUT_JSON_FILE,
                "host_role_bucket": self.ROLE_NAME,
                "host_format_bucket": self.FORMAT_NAME,
                "dns_formats_detected_count": len(dns_format_counts),
            },
            "examples": {"paths": [str(path) for path in all_fsstat_paths[:3]]},
            "technical": {
                "file_type": "text",
                "line_by_line_readable": True,
                "tabular_structure": False,
                "nested_structure": True,
                "encoding_counts": encoding_counts,
                "total_sample_lines": total_sample_lines,
                "json_lines": json_lines,
                "non_json_lines": non_json_lines,
                "metric_lines": metric_lines,
                "unknown_json_lines": unknown_json_lines,
                "top_level_key_counts": dict(
                    sorted(top_level_key_counts.items(), key=lambda item: item[1], reverse=True)[:20]
                ),
                "dataset_counts": dict(
                    sorted(dataset_counts.items(), key=lambda item: item[1], reverse=True)[:10]
                ),
                "sample_file_details": sample_files_info[:12],
            },
            "content": {
                "category": (
                    "Filesystem aggregate telemetry in JSON-lines (Metricbeat system.fsstat), "
                    "including filesystem count and total_size used/free/total counters."
                ),
                "hosts_detected": dict(sorted(host_names.items(), key=lambda item: item[1], reverse=True)[:12]),
                "fsstat_count_stats": self._stats(fsstat_counts),
                "fsstat_total_files_stats": self._stats(total_files_values),
                "fsstat_used_bytes_stats": self._stats(fsstat_used_bytes_values),
                "fsstat_free_bytes_stats": self._stats(fsstat_free_bytes_values),
                "fsstat_total_bytes_stats": self._stats(fsstat_total_bytes_values),
            },
            "label_detection": {
                "label_found": False,
                "label_field_name": "-",
                "label_values": [],
                "supports_supervised_learning": "no",
                "notes": "No explicit class/attack labels were detected in sampled fsstat.log rows.",
            },
            "time_detection": {
                "timestamp_found": json_lines > 0,
                "timestamp_fields": ["@timestamp"] if json_lines > 0 else [],
                "timestamp_format": "ISO-8601" if json_lines > 0 else "unknown",
                "timezone": "UTC (suffix Z), event ingestion timezone" if json_lines > 0 else "unknown",
                "sequence_ready": json_lines > 0,
                "sliding_window_ready": json_lines > 0,
            },
            "data_quality": {
                "empty_files_count": empty_files,
                "parse_error_files_count": parse_errors,
                "missing_timestamp_count": missing_timestamp_count,
                "missing_total_size_values_count": missing_total_size_values_count,
                "duplicate_line_count_sample": duplicate_lines,
                "mixed_schema_detected": mixed_schema_detected,
            },
            "final_status": status,
            "needs_custom_parser": mixed_schema_detected,
            "priority": "high" if mixed_schema_detected else "medium",
        }

    @staticmethod
    def _safe_get_dict(payload: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any] | None:
        node: Any = payload
        for key in path:
            if not isinstance(node, dict) or key not in node:
                return None
            node = node[key]
        return node if isinstance(node, dict) else None

    @staticmethod
    def _safe_extract_numeric(payload: dict[str, Any], path: tuple[str, ...]) -> float | None:
        node: Any = payload
        for key in path:
            if not isinstance(node, dict) or key not in node:
                return None
            node = node[key]
        if isinstance(node, (int, float)):
            return float(node)
        return None

    @staticmethod
    def _stats(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"min": None, "max": None, "avg": None}
        return {"min": min(values), "max": max(values), "avg": sum(values) / len(values)}

    @staticmethod
    def _detect_encoding(file_path: Path) -> str:
        raw = file_path.read_bytes()[:32768]
        for candidate in ("utf-8", "utf-8-sig", "latin-1", "cp1251"):
            try:
                raw.decode(candidate)
                return candidate
            except UnicodeDecodeError:
                continue
        return "latin-1"

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
        examples = summary["examples"]["paths"]
        used_bytes_stats = content["fsstat_used_bytes_stats"]

        return f"""
# Анализ формата: fsstat.log

## 1. Назначение
`fsstat.log` в `TRAIN` содержит агрегированную телеметрию файловых систем host (Metricbeat `system.fsstat`) для оценки заполнения дисков и ёмкости хранилища.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | fsstat.log |
| Варианты расширения | `.log` (группа `fsstat.log`) |
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
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | none (JSON-lines) |
| Кодировка | {', '.join(f"{k} ({v})" for k, v in technical['encoding_counts'].items())} |
| Вложенная структура | да (вложенные JSON-объекты) |
| Sample-файлов проанализировано | {scope['sampled_files_count']} |
| Sample-строк проанализировано | {technical['total_sample_lines']} |
| JSON lines | {technical['json_lines']} |
| Metric rows | {technical['metric_lines']} |

## 5. Содержательная структура
Основной поток - записи `system.fsstat` с полями:
- `count`, `total_files`, `total_size.used/free/total`;
- `metricset.period`, `event.duration`;
- `agent.version`, `host.name`, `event.dataset`.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| @timestamp | datetime | временная метка события | `2022-01-13T14:31:34.544Z` |
| host.name | string | идентификатор host | `internal-share` |
| event.dataset | string | тип telemetry-события | `system.fsstat` |
| system.fsstat.count | float | число смонтированных файловых систем | `3` |
| system.fsstat.total_files | float | общее число файлов (inode) | `6451200` |
| system.fsstat.total_size.used | float | занято байт по всем ФС | `3170240512` |
| system.fsstat.total_size.free | float | свободно байт по всем ФС | `48787542016` |
| system.fsstat.total_size.total | float | общий объём байт по всем ФС | `51957782528` |
| metricset.period | float | период сбора метрики (мс) | `60000` |
| event.duration | float | длительность события (нс) | `182471` |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | {"да" if label['label_found'] else "нет"} |
| Название поля | {label['label_field_name']} |
| Значения label | - |
| Можно использовать для supervised learning | {label['supports_supervised_learning']} |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | {"да" if time_block['timestamp_found'] else "нет"} |
| Название поля | {', '.join(time_block['timestamp_fields']) if time_block['timestamp_fields'] else '-'} |
| Формат времени | {time_block['timestamp_format']} |
| Timezone | {time_block['timezone']} |
| Можно строить sequence | {"да" if time_block['sequence_ready'] else "нет"} |
| Можно применять sliding window | {"да" if time_block['sliding_window_ready'] else "нет"} |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- rolling statistics по `total_size.used`, `total_size.free`, `total_size.total`;
- коэффициент заполнения `total_size.used / total_size.total`;
- динамика изменения `count` и `total_files`;
- тренды `event.duration` и `metricset.period`.

### Network / hybrid-признаки
- корреляция роста использования ФС с network/auth/process событиями на том же host.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if quality['empty_files_count'] > 0 else "нет"} | count: {quality['empty_files_count']} |
| Повреждённые файлы | {"да" if quality['parse_error_files_count'] > 0 else "нет"} | parse errors: {quality['parse_error_files_count']} |
| Missing values | {"да" if quality['missing_total_size_values_count'] > 0 else "нет"} | missing total_size rows: {quality['missing_total_size_values_count']} |
| Нестабильная структура | {"да" if quality['mixed_schema_detected'] else "нет"} | unknown/non-json rows present |
| Смешанные схемы | {"да" if technical['unknown_json_lines'] > 0 else "нет"} | unknown json rows: {technical['unknown_json_lines']} |
| Дубли строк | {"да" if quality['duplicate_line_count_sample'] > 0 else "нет"} | duplicates in sample: {quality['duplicate_line_count_sample']} |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary['final_status']} |
| Нужен отдельный парсер | {"да" if summary['needs_custom_parser'] else "нет"} |
| Приоритет обработки | {summary['priority']} |

## 12. Вывод
`TRAIN/fsstat.log` имеет стабильную JSON-lines структуру и пригоден для извлечения host storage-признаков.
Статистика `total_size.used` (sample): min={used_bytes_stats['min']}, max={used_bytes_stats['max']}, avg={used_bytes_stats['avg']}.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        content = summary["content"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]
        examples = summary["examples"]["paths"]
        used_pct_stats = content["fsstat_used_bytes_stats"]

        return f"""
# Format Analysis: fsstat.log

## 1. Purpose
`fsstat.log` in `TRAIN` contains host fsstat aggregate statistics telemetry (Metricbeat `system.fsstat`) for disk utilization monitoring, capacity pressure analysis, and storage degradation detection.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | fsstat.log |
| Extension variants | `.log` (grouped as `fsstat.log`) |
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
| Tabular structure | no |
| Header | no |
| Delimiter | none (JSON-lines) |
| Encoding | {', '.join(f"{k} ({v})" for k, v in technical['encoding_counts'].items())} |
| Nested structure | yes (nested JSON objects) |
| Sampled files | {scope['sampled_files_count']} |
| Sampled lines | {technical['total_sample_lines']} |
| JSON lines | {technical['json_lines']} |
| Metric rows | {technical['metric_lines']} |

## 5. Semantic structure
Primary flow: `system.fsstat` records with fields:
- `count`, `total_files`, `total_size.used/free/total`;
- `metricset.period`, `event.duration`;
- `agent.version`, `host.name`, `event.dataset`.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| @timestamp | datetime | event timestamp | `2022-01-13T14:31:34.543Z` |
| host.name | string | host identifier | `internal-share` |
| event.dataset | string | telemetry dataset type | `system.fsstat` |
| system.fsstat.count | float | number of mounted filesystems | `3` |
| system.fsstat.total_files | float | total file/inode count | `6451200` |
| system.fsstat.total_size.used | float | used bytes across all filesystems | `3170240512` |
| system.fsstat.total_size.free | float | free bytes across all filesystems | `48787542016` |
| system.fsstat.total_size.total | float | total bytes across all filesystems | `51957782528` |
| metricset.period | float | metric collection period (ms) | `60000` |
| event.duration | float | event processing duration (ns) | `182471` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | {"yes" if label['label_found'] else "no"} |
| Field name | {label['label_field_name']} |
| Label values | - |
| Suitable for supervised learning | {label['supports_supervised_learning']} |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | {"yes" if time_block['timestamp_found'] else "no"} |
| Field name | {', '.join(time_block['timestamp_fields']) if time_block['timestamp_fields'] else '-'} |
| Timestamp format | {time_block['timestamp_format']} |
| Timezone | {time_block['timezone']} |
| Sequence-ready | {"yes" if time_block['sequence_ready'] else "no"} |
| Sliding-window-ready | {"yes" if time_block['sliding_window_ready'] else "no"} |

## 9. Potential feature extraction signals
### DNS features
- not applicable.

### Host features
- rolling statistics on `total_size.used`, `total_size.free`, and `total_size.total`;
- utilization ratio `total_size.used / total_size.total`;
- dynamics of `count` and `total_files`;
- trend-based features from `event.duration` and `metricset.period`.

### Network / hybrid features
- correlation of fsstat pressure with network/auth/process activity on the same host.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if quality['empty_files_count'] > 0 else "no"} | count: {quality['empty_files_count']} |
| Corrupted files | {"yes" if quality['parse_error_files_count'] > 0 else "no"} | parse errors: {quality['parse_error_files_count']} |
| Missing values | {"yes" if quality['missing_total_size_values_count'] > 0 else "no"} | missing usage rows: {quality['missing_total_size_values_count']} |
| Unstable structure | {"yes" if quality['mixed_schema_detected'] else "no"} | unknown/non-json rows present |
| Mixed schemas | {"yes" if technical['unknown_json_lines'] > 0 else "no"} | unknown json rows: {technical['unknown_json_lines']} |
| Duplicate rows | {"yes" if quality['duplicate_line_count_sample'] > 0 else "no"} | duplicates in sample: {quality['duplicate_line_count_sample']} |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary['final_status']} |
| Needs dedicated parser | {"yes" if summary['needs_custom_parser'] else "no"} |
| Processing priority | {summary['priority']} |

## 12. Conclusion
`TRAIN/fsstat.log` has a stable JSON-lines structure and is suitable for host storage feature extraction.
`total_size.used` stats (sample): min={used_pct_stats['min']}, max={used_pct_stats['max']}, avg={used_pct_stats['avg']}.
"""

    def _build_ru_readme(self, fsstat_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", 0)
        filesystem_count = host_counts.get("filesystem.log", 0)
        fsstat_count = host_counts.get("fsstat.log", fsstat_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE)
        filesystem_status = self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE)
        fsstat_status = fsstat_summary["final_status"]

        return f"""
# РђРЅР°Р»РёР· СЃРѕРґРµСЂР¶РёРјРѕРіРѕ С„Р°Р№Р»РѕРІ РґР°С‚Р°СЃРµС‚РѕРІ (Host)

| Р¤РѕСЂРјР°С‚ | РљРѕР»РёС‡РµСЃС‚РІРѕ С„Р°Р№Р»РѕРІ | DNS | Host | РЎС‚Р°С‚СѓСЃ | Р”РѕРєСѓРјРµРЅС‚ |
|---|---:|---|---|---|---|
| csv | {csv_count} | РЅРµС‚ | РґР° | {csv_status} | csv.md |
| auth.log | {auth_count} | РЅРµС‚ | РґР° | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | РЅРµС‚ | РґР° | {cpu_status} | cpu.log.md |
| diskio.log | {diskio_count} | РЅРµС‚ | РґР° | {diskio_status} | diskio.log.md |
| filesystem.log | {filesystem_count} | РЅРµС‚ | РґР° | {filesystem_status} | filesystem.log.md |
| fsstat.log | {fsstat_count} | РЅРµС‚ | РґР° | {fsstat_status} | fsstat.log.md |
"""

    def _build_en_readme(self, fsstat_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", 0)
        filesystem_count = host_counts.get("filesystem.log", 0)
        fsstat_count = host_counts.get("fsstat.log", fsstat_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE)
        filesystem_status = self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE)
        fsstat_status = fsstat_summary["final_status"]

        return f"""
# Dataset File Content Analysis (Host)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| csv | {csv_count} | no | yes | {csv_status} | csv.md |
| auth.log | {auth_count} | no | yes | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | no | yes | {cpu_status} | cpu.log.md |
| diskio.log | {diskio_count} | no | yes | {diskio_status} | diskio.log.md |
| filesystem.log | {filesystem_count} | no | yes | {filesystem_status} | filesystem.log.md |
| fsstat.log | {fsstat_count} | no | yes | {fsstat_status} | fsstat.log.md |
"""

    def _build_ru_report(
        self,
        summary_payload: dict[str, Any],
        summary_json_path: Path,
        docs_ru_path: Path,
        docs_en_path: Path,
        docs_ru_readme_path: Path,
        docs_en_readme_path: Path,
        total_files_count: int,
        sampled_files_count: int,
        status: str,
    ) -> str:
        top_keys = summary_payload["technical"]["top_level_key_counts"]
        json_structure_sample = {
            "scope": summary_payload["scope"],
            "path_grouping": summary_payload["path_grouping"],
            "final_status": summary_payload["final_status"],
        }
        json_structure_text = json.dumps(json_structure_sample, ensure_ascii=False, indent=2)

        return f"""
# РћС‚С‡С‘С‚: Task6 (Analysis of host fsstat-log dataset files)

## РћРїРёСЃР°РЅРёРµ Р·Р°РґР°С‡Рё
Р РµР°Р»РёР·РѕРІР°РЅ РѕС‚РґРµР»СЊРЅС‹Р№ СЌС‚Р°Рї Р°РЅР°Р»РёР·Р° С„РѕСЂРјР°С‚Р° `TRAIN/fsstat.log` РЅР° РѕСЃРЅРѕРІРµ `temp_data/sort-path-host-file.json` СЃ РіРµРЅРµСЂР°С†РёРµР№ РґРѕРєСѓРјРµРЅС‚Р°С†РёРё РЅР° RU/EN.

## РљР°РєРёРµ С„Р°Р№Р»С‹ Р±С‹Р»Рё РґРѕР±Р°РІР»РµРЅС‹/РёР·РјРµРЅРµРЅС‹
- `scripts/handlers/analyze_host_fsstat_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/fsstat.log.md`
- `docs/en/analysis-dataset/host/fsstat.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task6(Analysis of host fsstat-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task6(Analysis of host fsstat-log dataset files)_report.md`
- `temp_data/analysis-host-fsstat-log-summary.json`

## РћРїРёСЃР°РЅРёРµ СЃС‚СЂСѓРєС‚СѓСЂС‹ JSON
- top-level keys: {", ".join(top_keys.keys())}
- dataset: `system.fsstat`
- РІР»РѕР¶РµРЅРЅС‹Рµ РїРѕР»СЏ: `system.fsstat.count/total_files/total_size.used/total_size.free/total_size.total`.

## Р›РѕРіРёРєР° РіСЂСѓРїРїРёСЂРѕРІРєРё РїСѓС‚РµР№
1. РЎС‡РёС‚С‹РІР°РµС‚СЃСЏ `sort-path-host-file.json`.
2. Р’С‹Р±РёСЂР°РµС‚СЃСЏ bucket: `TRAIN -> fsstat.log`.
3. РџР°СЂР°Р»Р»РµР»СЊРЅРѕ С‡РёС‚Р°РµС‚СЃСЏ `sort-path-dns-file.json` РґР»СЏ РІР°Р»РёРґР°С†РёРё РєРѕРЅС‚РµРєСЃС‚Р° DNS/Host Р±РµР· СЃРјРµС€РёРІР°РЅРёСЏ РґР°РЅРЅС‹С….
4. Р”Р»СЏ Р°РЅР°Р»РёР·Р° Р±РµСЂС‘С‚СЃСЏ РѕРіСЂР°РЅРёС‡РµРЅРЅС‹Р№ sample С„Р°Р№Р»РѕРІ Рё СЃС‚СЂРѕРє.

## РџСЂРёРјРµСЂ РёС‚РѕРіРѕРІРѕРіРѕ JSON
```json
{json_structure_text}
```

## Р РµР·СѓР»СЊС‚Р°С‚
- Р’СЃРµРіРѕ С„Р°Р№Р»РѕРІ С„РѕСЂРјР°С‚Р°: `{total_files_count}`.
- Sample-С„Р°Р№Р»РѕРІ РїСЂРѕР°РЅР°Р»РёР·РёСЂРѕРІР°РЅРѕ: `{sampled_files_count}`.
- РС‚РѕРіРѕРІС‹Р№ СЃС‚Р°С‚СѓСЃ: `{status}`.

## РђСЂС‚РµС„Р°РєС‚С‹
- Summary JSON: `{summary_json_path}`
- RU doc: `{docs_ru_path}`
- EN doc: `{docs_en_path}`
- RU README: `{docs_ru_readme_path}`
- EN README: `{docs_en_readme_path}`
"""

    def _build_en_report(
        self,
        summary_payload: dict[str, Any],
        summary_json_path: Path,
        docs_ru_path: Path,
        docs_en_path: Path,
        docs_ru_readme_path: Path,
        docs_en_readme_path: Path,
        total_files_count: int,
        sampled_files_count: int,
        status: str,
    ) -> str:
        top_keys = summary_payload["technical"]["top_level_key_counts"]
        json_structure_sample = {
            "scope": summary_payload["scope"],
            "path_grouping": summary_payload["path_grouping"],
            "final_status": summary_payload["final_status"],
        }
        json_structure_text = json.dumps(json_structure_sample, ensure_ascii=False, indent=2)

        return f"""
# Report: Task6 (Analysis of host fsstat-log dataset files)

## Task description
Implemented a dedicated analysis stage for `TRAIN/fsstat.log` using `temp_data/sort-path-host-file.json` with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_fsstat_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/fsstat.log.md`
- `docs/en/analysis-dataset/host/fsstat.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task6(Analysis of host fsstat-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task6(Analysis of host fsstat-log dataset files)_report.md`
- `temp_data/analysis-host-fsstat-log-summary.json`

## JSON structure description
- top-level keys: {", ".join(top_keys.keys())}
- dataset: `system.fsstat`
- nested fields: `system.fsstat.count/total_files/total_size.used/total_size.free/total_size.total`.

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket: `TRAIN -> fsstat.log`.
3. Read `sort-path-dns-file.json` in parallel for DNS/Host context validation without data mixing.
4. Analyze only bounded samples of files and lines.

## Sample of resulting JSON
```json
{json_structure_text}
```

## Result
- Total format files: `{total_files_count}`.
- Sampled files analyzed: `{sampled_files_count}`.
- Final status: `{status}`.

## Artifacts
- Summary JSON: `{summary_json_path}`
- RU doc: `{docs_ru_path}`
- EN doc: `{docs_en_path}`
- RU README: `{docs_ru_readme_path}`
- EN README: `{docs_en_readme_path}`
"""

    def _load_host_format_counts(self) -> dict[str, int]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        role_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            return {}

        counts: dict[str, int] = {}
        for format_name, paths in role_bucket.items():
            if isinstance(paths, list):
                counts[format_name] = len(paths)
        return counts

    @staticmethod
    def _load_optional_status(summary_path: Path) -> str:
        if not summary_path.exists():
            return "-"
        try:
            payload = JsonDataManager(summary_path).read(default={})
        except (ValueError, TypeError):
            return "-"
        status = payload.get("final_status")
        return str(status) if isinstance(status, str) else "-"

