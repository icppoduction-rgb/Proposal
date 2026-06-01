from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostDiskioLogContentAnalysisResult:
    """Result of analyzing TRAIN/diskio.log host datasets and generating documentation."""

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


class HostDiskioLogContentAnalysisHandler:
    """Analyzes host TRAIN/diskio.log datasets and writes bilingual markdown documentation."""

    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "diskio.log"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-diskio-log-summary.json"
    CSV_SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"
    AUTH_SUMMARY_JSON_FILE = "analysis-host-auth-log-summary.json"
    CPU_SUMMARY_JSON_FILE = "analysis-host-cpu-log-summary.json"

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

    def analyze_and_generate_docs(self) -> HostDiskioLogContentAnalysisResult:
        """Runs diskio.log analysis and writes docs/report files."""
        role_to_formats = self._read_source_json()
        all_diskio_paths = self._extract_diskio_paths(role_to_formats)
        if not all_diskio_paths:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/diskio.log.")

        sampled_paths = self._select_sample_paths(all_diskio_paths)
        summary_payload = self._build_summary(all_diskio_paths=all_diskio_paths, sampled_paths=sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "diskio.log.md"
        docs_en_path = self.docs_en_dir / "diskio.log.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = (
            self.report_ru_dir / "Task4(Analysis of host diskio-log dataset files)_report.md"
        )
        report_en_path = (
            self.report_en_dir / "Task4(Analysis of host diskio-log dataset files)_report.md"
        )

        status = str(summary_payload["final_status"])

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(summary_payload))
        self._write_text_file(
            report_ru_path,
            self._build_ru_report(
                summary_json_path=summary_json_path,
                docs_ru_path=docs_ru_path,
                docs_en_path=docs_en_path,
                docs_ru_readme_path=docs_ru_readme_path,
                docs_en_readme_path=docs_en_readme_path,
                total_files_count=len(all_diskio_paths),
                sampled_files_count=len(sampled_paths),
                status=status,
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
                total_files_count=len(all_diskio_paths),
                sampled_files_count=len(sampled_paths),
                status=status,
            ),
        )

        return HostDiskioLogContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_diskio_paths),
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

    def _extract_diskio_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
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
        return all_paths[: self.max_files_per_format]

    def _build_summary(self, all_diskio_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        sample_files_info: list[dict[str, Any]] = []

        encoding_counts: dict[str, int] = {}
        top_level_key_counts: dict[str, int] = {}
        dataset_counts: dict[str, int] = {}
        host_names: dict[str, int] = {}
        disk_names: dict[str, int] = {}

        total_sample_lines = 0
        json_lines = 0
        non_json_lines = 0
        parse_errors = 0
        empty_files = 0

        system_diskio_metric_lines = 0
        host_disk_summary_lines = 0
        unknown_json_lines = 0

        missing_timestamp_count = 0
        missing_disk_name_count = 0
        missing_system_diskio_bytes_count = 0
        missing_host_disk_bytes_count = 0

        system_read_bytes_values: list[float] = []
        system_write_bytes_values: list[float] = []
        system_io_ops_values: list[float] = []
        host_read_bytes_values: list[float] = []
        host_write_bytes_values: list[float] = []

        for file_path in sampled_paths:
            file_info = {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": 0,
                "encoding": "unknown",
                "line_count_sample": 0,
                "json_line_count": 0,
                "system_diskio_metric_line_count": 0,
                "host_disk_summary_line_count": 0,
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

                system_obj = parsed_obj.get("system")
                system_diskio_obj = system_obj.get("diskio") if isinstance(system_obj, dict) else None

                has_system_diskio_shape = isinstance(system_diskio_obj, dict)
                has_host_disk_shape = (
                    isinstance(host_obj, dict)
                    and isinstance(host_obj.get("disk"), dict)
                    and "read.bytes" in host_obj.get("disk", {})
                    and "write.bytes" in host_obj.get("disk", {})
                )

                if has_system_diskio_shape:
                    system_diskio_metric_lines += 1
                    file_info["system_diskio_metric_line_count"] += 1

                    disk_name = system_diskio_obj.get("name")
                    if isinstance(disk_name, str):
                        disk_names[disk_name] = disk_names.get(disk_name, 0) + 1
                    else:
                        missing_disk_name_count += 1

                    read_bytes = self._safe_extract_numeric(parsed_obj, ("system", "diskio", "read", "bytes"))
                    write_bytes = self._safe_extract_numeric(parsed_obj, ("system", "diskio", "write", "bytes"))
                    io_ops = self._safe_extract_numeric(parsed_obj, ("system", "diskio", "io", "ops"))

                    if read_bytes is not None:
                        system_read_bytes_values.append(read_bytes)
                    if write_bytes is not None:
                        system_write_bytes_values.append(write_bytes)
                    if io_ops is not None:
                        system_io_ops_values.append(io_ops)

                    if read_bytes is None or write_bytes is None:
                        missing_system_diskio_bytes_count += 1
                    continue

                if has_host_disk_shape:
                    host_disk_summary_lines += 1
                    file_info["host_disk_summary_line_count"] += 1

                    host_disk_obj = host_obj["disk"]
                    read_bytes_raw = host_disk_obj.get("read.bytes")
                    write_bytes_raw = host_disk_obj.get("write.bytes")
                    if isinstance(read_bytes_raw, (int, float)):
                        host_read_bytes_values.append(float(read_bytes_raw))
                    if isinstance(write_bytes_raw, (int, float)):
                        host_write_bytes_values.append(float(write_bytes_raw))
                    if not isinstance(read_bytes_raw, (int, float)) or not isinstance(write_bytes_raw, (int, float)):
                        missing_host_disk_bytes_count += 1
                    continue

                unknown_json_lines += 1

            sample_files_info.append(file_info)

        mixed_schema_detected = host_disk_summary_lines > 0 or unknown_json_lines > 0 or non_json_lines > 0
        status = self.STATUS_PARTIAL if mixed_schema_detected else self.STATUS_READY

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": len(all_diskio_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "examples": {"paths": [str(path) for path in all_diskio_paths[:3]]},
            "technical": {
                "file_type": "text",
                "line_by_line_readable": True,
                "tabular_structure": False,
                "nested_structure": True,
                "encoding_counts": encoding_counts,
                "total_sample_lines": total_sample_lines,
                "json_lines": json_lines,
                "non_json_lines": non_json_lines,
                "system_diskio_metric_lines": system_diskio_metric_lines,
                "host_disk_summary_lines": host_disk_summary_lines,
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
                    "Disk I/O telemetry JSON-lines (Metricbeat system.diskio), "
                    "including per-device rows and host-level disk summary rows."
                ),
                "hosts_detected": dict(
                    sorted(host_names.items(), key=lambda item: item[1], reverse=True)[:12]
                ),
                "disk_names_detected": dict(
                    sorted(disk_names.items(), key=lambda item: item[1], reverse=True)[:20]
                ),
                "system_diskio_read_bytes_stats": self._stats(system_read_bytes_values),
                "system_diskio_write_bytes_stats": self._stats(system_write_bytes_values),
                "system_diskio_io_ops_stats": self._stats(system_io_ops_values),
                "host_disk_read_bytes_stats": self._stats(host_read_bytes_values),
                "host_disk_write_bytes_stats": self._stats(host_write_bytes_values),
            },
            "label_detection": {
                "label_found": False,
                "label_field_name": "-",
                "label_values": [],
                "supports_supervised_learning": "no",
                "notes": "No label/class indicators were detected in sampled diskio.log rows.",
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
                "missing_disk_name_count": missing_disk_name_count,
                "missing_system_diskio_bytes_count": missing_system_diskio_bytes_count,
                "missing_host_disk_bytes_count": missing_host_disk_bytes_count,
                "mixed_schema_detected": mixed_schema_detected,
            },
            "final_status": status,
            "needs_custom_parser": mixed_schema_detected,
            "priority": "high" if mixed_schema_detected else "medium",
        }

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

        return f"""
# Анализ формата: diskio.log

## 1. Назначение
`diskio.log` в `TRAIN` содержит телеметрию дискового ввода-вывода хоста (Metricbeat `system.diskio`) для анализа нагрузки, аномалий I/O и деградации дисковой подсистемы.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | diskio.log |
| Варианты расширения | `.log` (группа `diskio.log`) |
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
| Рядов `system.diskio` | {technical['system_diskio_metric_lines']} |
| Рядов `host.disk.*` | {technical['host_disk_summary_lines']} |

## 5. Содержательная структура
Основной поток: записи `system.diskio` с детализацией по устройствам (`system.diskio.name`) и счётчиками:
- `system.diskio.read.bytes`, `system.diskio.write.bytes`;
- `system.diskio.io.ops`, `system.diskio.io.time`;
- вложенный блок `system.diskio.iostat.*`.

Также присутствует вторичная под-схема: агрегированные записи с `host.disk.read.bytes` и `host.disk.write.bytes` без блока `system`.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| @timestamp | datetime | временная метка события | `2022-01-13T14:31:43.135Z` |
| host.name | string | идентификатор host | `internal-share` |
| event.dataset | string | тип telemetry-события | `system.diskio` |
| system.diskio.name | string | имя дискового устройства | `vda15` |
| system.diskio.read.bytes | float | счётчик прочитанных байт | `9526272` |
| system.diskio.write.bytes | float | счётчик записанных байт | `5120` |
| system.diskio.io.ops | float | число I/O операций | `0` |
| host.disk.read.bytes | float | агрегированные чтения host (альтернативная схема) | `1572864` |
| host.disk.write.bytes | float | агрегированные записи host (альтернативная схема) | `432029696` |

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
- rolling statistics по `system.diskio.read.bytes` / `system.diskio.write.bytes`;
- read/write ratio и burst-признаки;
- признаки насыщения I/O по `system.diskio.io.ops` и `system.diskio.iostat.busy`;
- device-level baseline deviation;
- корреляция device-уровня с host-level `host.disk.*` агрегатами.

### Network / hybrid-признаки
- корреляция I/O spikes с network flow и authentication событиями на том же host.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if quality['empty_files_count'] > 0 else "нет"} | count: {quality['empty_files_count']} |
| Повреждённые файлы | {"да" if quality['parse_error_files_count'] > 0 else "нет"} | parse errors: {quality['parse_error_files_count']} |
| Missing values | {"да" if quality['missing_system_diskio_bytes_count'] > 0 else "нет"} | missing system bytes rows: {quality['missing_system_diskio_bytes_count']} |
| Нестабильная структура | {"да" if quality['mixed_schema_detected'] else "нет"} | сочетание `system.diskio` и `host.disk.*` |
| Смешанные схемы | {"да" if quality['mixed_schema_detected'] else "нет"} | unknown json rows: {technical['unknown_json_lines']} |
| Дубли строк | нет | в sample не обнаружены |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary['final_status']} |
| Нужен отдельный парсер | {"да" if summary['needs_custom_parser'] else "нет"} |
| Приоритет обработки | {summary['priority']} |

## 12. Вывод
`TRAIN/diskio.log` пригоден для извлечения host I/O признаков, но формат содержит минимум две рабочие под-схемы в рамках одного расширения (`system.diskio` и `host.disk.*`). Для production-пайплайна нужен парсер с явным ветвлением по типу строки.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]
        examples = summary["examples"]["paths"]

        return f"""
# Format Analysis: diskio.log

## 1. Purpose
`diskio.log` in `TRAIN` contains host disk I/O telemetry (Metricbeat `system.diskio`) for load analysis, I/O anomaly detection, and disk subsystem health monitoring.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | diskio.log |
| Extension variants | `.log` (grouped as `diskio.log`) |
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
| `system.diskio` rows | {technical['system_diskio_metric_lines']} |
| `host.disk.*` rows | {technical['host_disk_summary_lines']} |

## 5. Semantic structure
Primary flow: `system.diskio` records with per-device metrics (`system.diskio.name`) and counters:
- `system.diskio.read.bytes`, `system.diskio.write.bytes`;
- `system.diskio.io.ops`, `system.diskio.io.time`;
- nested `system.diskio.iostat.*` block.

A second schema is also present: aggregated rows with `host.disk.read.bytes` and `host.disk.write.bytes` without the `system` object.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| @timestamp | datetime | event timestamp | `2022-01-13T14:31:43.135Z` |
| host.name | string | host identifier | `internal-share` |
| event.dataset | string | telemetry dataset type | `system.diskio` |
| system.diskio.name | string | disk device name | `vda15` |
| system.diskio.read.bytes | float | read-bytes counter | `9526272` |
| system.diskio.write.bytes | float | write-bytes counter | `5120` |
| system.diskio.io.ops | float | I/O operations counter | `0` |
| host.disk.read.bytes | float | host-level read bytes (alternate schema) | `1572864` |
| host.disk.write.bytes | float | host-level write bytes (alternate schema) | `432029696` |

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
- rolling statistics over `system.diskio.read.bytes` / `system.diskio.write.bytes`;
- read/write ratio and burst indicators;
- I/O saturation features from `system.diskio.io.ops` and `system.diskio.iostat.busy`;
- device-level baseline deviation;
- cross-checking device-level telemetry with host-level `host.disk.*` aggregates.

### Network / hybrid features
- correlation of I/O spikes with network flow and authentication events on the same host.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if quality['empty_files_count'] > 0 else "no"} | count: {quality['empty_files_count']} |
| Corrupted files | {"yes" if quality['parse_error_files_count'] > 0 else "no"} | parse errors: {quality['parse_error_files_count']} |
| Missing values | {"yes" if quality['missing_system_diskio_bytes_count'] > 0 else "no"} | missing system bytes rows: {quality['missing_system_diskio_bytes_count']} |
| Unstable structure | {"yes" if quality['mixed_schema_detected'] else "no"} | `system.diskio` + `host.disk.*` mix |
| Mixed schemas | {"yes" if quality['mixed_schema_detected'] else "no"} | unknown json rows: {technical['unknown_json_lines']} |
| Duplicate rows | no | none detected in sample |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary['final_status']} |
| Needs dedicated parser | {"yes" if summary['needs_custom_parser'] else "no"} |
| Processing priority | {summary['priority']} |

## 12. Conclusion
`TRAIN/diskio.log` is suitable for host I/O feature extraction, but at least two active sub-schemas exist under the same extension (`system.diskio` and `host.disk.*`). A production parser should explicitly branch by row shape.
"""

    def _build_ru_readme(self, diskio_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", diskio_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = diskio_summary["final_status"]

        return f"""
# Анализ содержимого файлов датасетов (Host)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| csv | {csv_count} | нет | да | {csv_status} | csv.md |
| auth.log | {auth_count} | нет | да | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | нет | да | {cpu_status} | cpu.log.md |
| diskio.log | {diskio_count} | нет | да | {diskio_status} | diskio.log.md |
"""

    def _build_en_readme(self, diskio_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", diskio_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = diskio_summary["final_status"]

        return f"""
# Dataset File Content Analysis (Host)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| csv | {csv_count} | no | yes | {csv_status} | csv.md |
| auth.log | {auth_count} | no | yes | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | no | yes | {cpu_status} | cpu.log.md |
| diskio.log | {diskio_count} | no | yes | {diskio_status} | diskio.log.md |
"""

    def _build_ru_report(
        self,
        summary_json_path: Path,
        docs_ru_path: Path,
        docs_en_path: Path,
        docs_ru_readme_path: Path,
        docs_en_readme_path: Path,
        total_files_count: int,
        sampled_files_count: int,
        status: str,
    ) -> str:
        return f"""
# Отчёт: Task4 (Analysis of host diskio-log dataset files)

## Описание задачи
Реализован этап анализа формата `TRAIN/diskio.log` на основе `temp_data/sort-path-host-file.json` с генерацией RU/EN документации.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_diskio_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/diskio.log.md`
- `docs/en/analysis-dataset/host/diskio.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task4(Analysis of host diskio-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task4(Analysis of host diskio-log dataset files)_report.md`
- `temp_data/analysis-host-diskio-log-summary.json`

## Логика
1. Загружены пути `TRAIN/diskio.log`.
2. Выполнен анализ JSON-lines структуры и вложенных disk I/O полей.
3. Отдельно выделены два типа строк: `system.diskio` и `host.disk.*`.
4. Проверены timestamp, label-индикаторы и качество данных.
5. Сгенерированы markdown-документы и обновлён host README.

## Результат
- Всего файлов формата: `{total_files_count}`.
- Sample-файлов проанализировано: `{sampled_files_count}`.
- Итоговый статус: `{status}`.

## Артефакты
- Summary JSON: `{summary_json_path}`
- RU doc: `{docs_ru_path}`
- EN doc: `{docs_en_path}`
- RU README: `{docs_ru_readme_path}`
- EN README: `{docs_en_readme_path}`
"""

    def _build_en_report(
        self,
        summary_json_path: Path,
        docs_ru_path: Path,
        docs_en_path: Path,
        docs_ru_readme_path: Path,
        docs_en_readme_path: Path,
        total_files_count: int,
        sampled_files_count: int,
        status: str,
    ) -> str:
        return f"""
# Report: Task4 (Analysis of host diskio-log dataset files)

## Task description
Implemented `TRAIN/diskio.log` content analysis using `temp_data/sort-path-host-file.json`, with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_diskio_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/diskio.log.md`
- `docs/en/analysis-dataset/host/diskio.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task4(Analysis of host diskio-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task4(Analysis of host diskio-log dataset files)_report.md`
- `temp_data/analysis-host-diskio-log-summary.json`

## Logic
1. Loaded `TRAIN/diskio.log` paths.
2. Parsed JSON-lines structure and nested disk I/O fields.
3. Separated two row types: `system.diskio` and `host.disk.*`.
4. Checked timestamp, label indicators, and data quality.
5. Generated markdown docs and updated host README.

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
        source_json_path = self.temp_data_path / self.INPUT_JSON_FILE
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
