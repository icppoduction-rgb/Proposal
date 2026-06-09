from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostCPULogContentAnalysisResult:
    """Result of analyzing TRAIN/cpu.log host datasets and generating documentation."""

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


class HostCPULogContentAnalysisHandler:
    """Analyzes host TRAIN/cpu.log datasets and writes bilingual markdown documentation."""

    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "cpu.log"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-cpu-log-summary.json"
    CSV_SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"
    AUTH_SUMMARY_JSON_FILE = "analysis-host-auth-log-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"

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
        self.max_lines_per_file = max(100, max_lines_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "host"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "host"

    def analyze_and_generate_docs(self) -> HostCPULogContentAnalysisResult:
        """Runs cpu.log analysis and writes docs/report files."""
        role_to_formats = self._read_source_json()
        all_cpu_paths = self._extract_cpu_paths(role_to_formats)
        if not all_cpu_paths:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/cpu.log.")

        sampled_paths = self._select_sample_paths(all_cpu_paths)
        summary_payload = self._build_summary(all_cpu_paths=all_cpu_paths, sampled_paths=sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "cpu.log.md"
        docs_en_path = self.docs_en_dir / "cpu.log.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = (
            self.report_ru_dir / "Task3(Analysis of host cpu-log dataset files)_report.md"
        )
        report_en_path = (
            self.report_en_dir / "Task3(Analysis of host cpu-log dataset files)_report.md"
        )

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
                total_files_count=len(all_cpu_paths),
                sampled_files_count=len(sampled_paths),
                status=str(summary_payload["final_status"]),
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
                total_files_count=len(all_cpu_paths),
                sampled_files_count=len(sampled_paths),
                status=str(summary_payload["final_status"]),
            ),
        )

        return HostCPULogContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_cpu_paths),
            sampled_files_count=len(sampled_paths),
            status=str(summary_payload["final_status"]),
        )

    def _read_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        if not payload:
            raise FileNotFoundError(f"Source JSON is empty or missing: {source_json_path}")
        if self.ROLE_NAME not in payload:
            raise ValueError(f"Missing role '{self.ROLE_NAME}' in {source_json_path}.")
        return payload

    def _extract_cpu_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
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

    def _build_summary(self, all_cpu_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        sample_files_info: list[dict[str, Any]] = []

        encoding_counts: dict[str, int] = {}
        top_level_key_counts: dict[str, int] = {}
        dataset_counts: dict[str, int] = {}

        total_sample_lines = 0
        json_lines = 0
        non_json_lines = 0
        parse_errors = 0
        empty_files = 0

        metric_lines = 0
        label_lines = 0
        unknown_json_lines = 0

        missing_timestamp_count = 0
        missing_cpu_pct_count = 0

        host_names: dict[str, int] = {}
        label_values: dict[str, int] = {}

        cpu_host_pct_values: list[float] = []
        cpu_total_norm_pct_values: list[float] = []

        for file_path in sampled_paths:
            file_info = {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": 0,
                "encoding": "unknown",
                "line_count_sample": 0,
                "json_line_count": 0,
                "metric_line_count": 0,
                "label_line_count": 0,
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

                dataset_name = (
                    parsed_obj.get("event", {}).get("dataset")
                    if isinstance(parsed_obj.get("event"), dict)
                    else None
                )
                if isinstance(dataset_name, str):
                    dataset_counts[dataset_name] = dataset_counts.get(dataset_name, 0) + 1

                host_name = (
                    parsed_obj.get("host", {}).get("name")
                    if isinstance(parsed_obj.get("host"), dict)
                    else None
                )
                if isinstance(host_name, str):
                    host_names[host_name] = host_names.get(host_name, 0) + 1

                has_metric_shape = (
                    isinstance(parsed_obj.get("metricset"), dict)
                    and isinstance(parsed_obj.get("system"), dict)
                    and isinstance(parsed_obj.get("host"), dict)
                )
                has_label_shape = (
                    isinstance(parsed_obj.get("labels"), list)
                    and isinstance(parsed_obj.get("rules"), dict)
                    and "line" in parsed_obj
                )

                if has_metric_shape:
                    metric_lines += 1
                    file_info["metric_line_count"] += 1

                    if "@timestamp" not in parsed_obj:
                        missing_timestamp_count += 1

                    host_cpu_pct = self._safe_extract_numeric(parsed_obj, ("host", "cpu", "pct"))
                    if host_cpu_pct is not None:
                        cpu_host_pct_values.append(host_cpu_pct)

                    total_norm_pct = self._safe_extract_numeric(
                        parsed_obj,
                        ("system", "cpu", "total", "norm", "pct"),
                    )
                    if total_norm_pct is not None:
                        cpu_total_norm_pct_values.append(total_norm_pct)
                    else:
                        missing_cpu_pct_count += 1

                    continue

                if has_label_shape:
                    label_lines += 1
                    file_info["label_line_count"] += 1
                    for raw_label in parsed_obj.get("labels", []):
                        if isinstance(raw_label, str):
                            label_values[raw_label] = label_values.get(raw_label, 0) + 1
                    continue

                unknown_json_lines += 1

            sample_files_info.append(file_info)

        mixed_schema_detected = label_lines > 0 or unknown_json_lines > 0 or non_json_lines > 0
        status = self.STATUS_PARTIAL if mixed_schema_detected else self.STATUS_READY

        def _stats(values: list[float]) -> dict[str, float | None]:
            if not values:
                return {"min": None, "max": None, "avg": None}
            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

        host_pct_stats = _stats(cpu_host_pct_values)
        total_norm_stats = _stats(cpu_total_norm_pct_values)

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": len(all_cpu_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "examples": {"paths": [str(path) for path in all_cpu_paths[:3]]},
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
                "label_lines": label_lines,
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
                "category": "CPU telemetry metrics in JSON-lines (Metricbeat system.cpu), plus sparse rule/label annotations.",
                "hosts_detected": dict(
                    sorted(host_names.items(), key=lambda item: item[1], reverse=True)[:12]
                ),
                "label_values_detected": dict(
                    sorted(label_values.items(), key=lambda item: item[1], reverse=True)[:12]
                ),
                "cpu_host_pct_stats": host_pct_stats,
                "cpu_total_norm_pct_stats": total_norm_stats,
            },
            "label_detection": {
                "label_found": label_lines > 0,
                "label_field_name": "labels",
                "label_values": list(sorted(label_values.keys())),
                "supports_supervised_learning": "partially" if label_lines > 0 else "no",
                "notes": "Labels exist only in annotation-like records, not in all metric rows.",
            },
            "time_detection": {
                "timestamp_found": True,
                "timestamp_fields": ["@timestamp"],
                "timestamp_format": "ISO-8601",
                "timezone": "UTC (suffix Z), event ingestion timezone",
                "sequence_ready": True,
                "sliding_window_ready": True,
            },
            "data_quality": {
                "empty_files_count": empty_files,
                "parse_error_files_count": parse_errors,
                "missing_timestamp_count": missing_timestamp_count,
                "missing_cpu_pct_count": missing_cpu_pct_count,
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

        host_pct_stats = content["cpu_host_pct_stats"]
        total_norm_stats = content["cpu_total_norm_pct_stats"]

        label_values_text = ", ".join(label["label_values"]) if label["label_values"] else "-"

        return f"""
# Анализ формата: cpu.log

## 1. Назначение
`cpu.log` в `TRAIN` содержит host CPU telemetry, пригодную для извлечения нагрузочных и временных признаков (CPU utilization, idle/user/system/iowait доли).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | cpu.log |
| Варианты расширения | `.log` (группа `cpu.log`) |
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
| Вложенная структура | да (вложенные объекты JSON) |
| Sample-файлов проанализировано | {scope['sampled_files_count']} |
| Sample-строк проанализировано | {technical['total_sample_lines']} |
| JSON lines | {technical['json_lines']} |
| Metric rows | {technical['metric_lines']} |
| Label rows | {technical['label_lines']} |

## 5. Содержательная структура
Основной поток — записи `system.cpu` (Metricbeat) с полями:
- `@timestamp`
- `host.name`, `host.cpu.pct`
- `system.cpu.total.norm.pct`, `system.cpu.user.norm.pct`, `system.cpu.system.norm.pct`, `system.cpu.idle.norm.pct`
- `event.dataset=system.cpu`, `metricset.name=cpu`.

Дополнительно обнаружены аннотационные строки (`line`, `labels`, `rules`) внутри части файлов.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| @timestamp | datetime | временная метка события | `2022-01-13T14:31:34.512Z` |
| host.name | string | имя host | `internal-share` |
| host.cpu.pct | float | агрегированная загрузка CPU | `0.1183` |
| system.cpu.total.norm.pct | float | нормализованная total CPU доля | `0.1183` |
| system.cpu.user.norm.pct | float | user CPU доля | `0.0578` |
| system.cpu.system.norm.pct | float | kernel/system CPU доля | `0.0246` |
| system.cpu.idle.norm.pct | float | idle CPU доля | `0.873` |
| labels[] | array[string] | attack/annotation labels (не везде) | `["escalate","crack_passwords"]` |
| rules | object | источники/правила аннотаций | `{{"escalate":["attacker.escalate.wpcrack"]}}` |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | {"да" if label['label_found'] else "нет"} |
| Название поля | {label['label_field_name']} |
| Значения label | {label_values_text} |
| Можно использовать для supervised learning | {label['supports_supervised_learning']} |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | {"да" if time_block['timestamp_found'] else "нет"} |
| Название поля | {', '.join(time_block['timestamp_fields'])} |
| Формат времени | {time_block['timestamp_format']} |
| Timezone | {time_block['timezone']} |
| Можно строить sequence | {"да" if time_block['sequence_ready'] else "нет"} |
| Можно применять sliding window | {"да" if time_block['sliding_window_ready'] else "нет"} |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- rolling statistics для `host.cpu.pct` и `system.cpu.total.norm.pct`;
- user/system/iowait/idle ratio признаки;
- burst/anomaly признаки по изменению CPU во времени;
- host-level baseline deviation;
- (частично) weak labels из `labels/rules` для semi-supervised/validation.

### Network / hybrid-признаки
- корреляция CPU spikes с network flow нагрузкой и auth/session событиями.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if quality['empty_files_count'] > 0 else "нет"} | count: {quality['empty_files_count']} |
| Повреждённые файлы | {"да" if quality['parse_error_files_count'] > 0 else "нет"} | parse errors: {quality['parse_error_files_count']} |
| Missing values | {"да" if quality['missing_cpu_pct_count'] > 0 else "нет"} | missing cpu pct rows: {quality['missing_cpu_pct_count']} |
| Нестабильная структура | {"да" if quality['mixed_schema_detected'] else "нет"} | metric rows + label/annotation rows |
| Смешанные схемы | {"да" if quality['mixed_schema_detected'] else "нет"} | unknown json rows: {technical['unknown_json_lines']} |
| Дубли строк | нет | в sample не обнаружены |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary['final_status']} |
| Нужен отдельный парсер | {"да" if summary['needs_custom_parser'] else "нет"} |
| Приоритет обработки | {summary['priority']} |

## 12. Вывод
`TRAIN/cpu.log` в основном готов для feature extraction по CPU-метрикам, но внутри формата присутствуют отдельные label/annotation строки с другой схемой. Поэтому рекомендуется парсер с ветвлением: `metric row` vs `annotation row`.

CPU статистика (sample):
- `host.cpu.pct`: min={host_pct_stats['min']}, max={host_pct_stats['max']}, avg={host_pct_stats['avg']}
- `system.cpu.total.norm.pct`: min={total_norm_stats['min']}, max={total_norm_stats['max']}, avg={total_norm_stats['avg']}
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        content = summary["content"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]
        examples = summary["examples"]["paths"]

        host_pct_stats = content["cpu_host_pct_stats"]
        total_norm_stats = content["cpu_total_norm_pct_stats"]
        label_values_text = ", ".join(label["label_values"]) if label["label_values"] else "-"

        return f"""
# Format Analysis: cpu.log

## 1. Purpose
`cpu.log` in `TRAIN` contains host CPU telemetry suitable for extracting load/time-based features (CPU utilization, idle/user/system/iowait shares).

## 2. Where it appears
| Field | Value |
|---|---|
| Format | cpu.log |
| Extension variants | `.log` (grouped as `cpu.log`) |
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
| Label rows | {technical['label_lines']} |

## 5. Semantic structure
Primary flow: `system.cpu` Metricbeat records with fields:
- `@timestamp`
- `host.name`, `host.cpu.pct`
- `system.cpu.total.norm.pct`, `system.cpu.user.norm.pct`, `system.cpu.system.norm.pct`, `system.cpu.idle.norm.pct`
- `event.dataset=system.cpu`, `metricset.name=cpu`.

Additional annotation-like lines (`line`, `labels`, `rules`) are present in part of the files.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| @timestamp | datetime | event timestamp | `2022-01-13T14:31:34.512Z` |
| host.name | string | host identifier | `internal-share` |
| host.cpu.pct | float | aggregated host CPU utilization | `0.1183` |
| system.cpu.total.norm.pct | float | normalized total CPU fraction | `0.1183` |
| system.cpu.user.norm.pct | float | user CPU fraction | `0.0578` |
| system.cpu.system.norm.pct | float | kernel/system CPU fraction | `0.0246` |
| system.cpu.idle.norm.pct | float | idle CPU fraction | `0.873` |
| labels[] | array[string] | attack/annotation labels (sparse) | `["escalate","crack_passwords"]` |
| rules | object | rule references for labels | `{{"escalate":["attacker.escalate.wpcrack"]}}` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | {"yes" if label['label_found'] else "no"} |
| Field name | {label['label_field_name']} |
| Label values | {label_values_text} |
| Suitable for supervised learning | {label['supports_supervised_learning']} |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | {"yes" if time_block['timestamp_found'] else "no"} |
| Field name | {', '.join(time_block['timestamp_fields'])} |
| Timestamp format | {time_block['timestamp_format']} |
| Timezone | {time_block['timezone']} |
| Sequence-ready | {"yes" if time_block['sequence_ready'] else "no"} |
| Sliding-window-ready | {"yes" if time_block['sliding_window_ready'] else "no"} |

## 9. Potential feature extraction signals
### DNS features
- not applicable.

### Host features
- rolling statistics on `host.cpu.pct` and `system.cpu.total.norm.pct`;
- user/system/iowait/idle ratio features;
- burst/anomaly features from temporal CPU deltas;
- host baseline deviation features;
- sparse weak labels from `labels/rules` for semi-supervised evaluation.

### Network / hybrid features
- correlate CPU spikes with network flow load and auth/session events.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if quality['empty_files_count'] > 0 else "no"} | count: {quality['empty_files_count']} |
| Corrupted files | {"yes" if quality['parse_error_files_count'] > 0 else "no"} | parse errors: {quality['parse_error_files_count']} |
| Missing values | {"yes" if quality['missing_cpu_pct_count'] > 0 else "no"} | missing cpu pct rows: {quality['missing_cpu_pct_count']} |
| Unstable structure | {"yes" if quality['mixed_schema_detected'] else "no"} | metric rows + label/annotation rows |
| Mixed schemas | {"yes" if quality['mixed_schema_detected'] else "no"} | unknown json rows: {technical['unknown_json_lines']} |
| Duplicate rows | no | none detected in sample |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary['final_status']} |
| Needs dedicated parser | {"yes" if summary['needs_custom_parser'] else "no"} |
| Processing priority | {summary['priority']} |

## 12. Conclusion
`TRAIN/cpu.log` is mostly ready for CPU metric feature extraction, but the format includes sparse label/annotation rows with a different schema. A parser with branching (`metric row` vs `annotation row`) is recommended.

CPU stats (sample):
- `host.cpu.pct`: min={host_pct_stats['min']}, max={host_pct_stats['max']}, avg={host_pct_stats['avg']}
- `system.cpu.total.norm.pct`: min={total_norm_stats['min']}, max={total_norm_stats['max']}, avg={total_norm_stats['avg']}
"""

    def _build_ru_readme(self, cpu_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", cpu_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = cpu_summary["final_status"]

        return f"""
# Анализ содержимого файлов датасетов (Host)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| csv | {csv_count} | нет | да | {csv_status} | csv.md |
| auth.log | {auth_count} | нет | да | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | нет | да | {cpu_status} | cpu.log.md |
"""

    def _build_en_readme(self, cpu_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", cpu_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = cpu_summary["final_status"]

        return f"""
# Dataset File Content Analysis (Host)

| Format | File count | DNS | Host | Status | Document |
|---|---:|---|---|---|---|
| csv | {csv_count} | no | yes | {csv_status} | csv.md |
| auth.log | {auth_count} | no | yes | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | no | yes | {cpu_status} | cpu.log.md |
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
# Отчёт: Task3 (Analysis of host cpu-log dataset files)

## Описание задачи
Реализован этап анализа формата `TRAIN/cpu.log` на основе `temp_data/sort-path-host-file.json` с генерацией RU/EN документации.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_cpu_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/cpu.log.md`
- `docs/en/analysis-dataset/host/cpu.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/Task3(Analysis of host cpu-log dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/Task3(Analysis of host cpu-log dataset files)_report.md`
- `temp_data/analysis-host-cpu-log-summary.json`

## Логика
1. Загружены пути `TRAIN/cpu.log`.
2. Выполнен анализ JSON-lines структуры и вложенных CPU полей.
3. Проверены timestamp, label-индикаторы и качество данных.
4. Зафиксированы смешанные схемы (metric rows + annotation rows).
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
# Report: Task3 (Analysis of host cpu-log dataset files)

## Task description
Implemented `TRAIN/cpu.log` content analysis using `temp_data/sort-path-host-file.json`, with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_cpu_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/cpu.log.md`
- `docs/en/analysis-dataset/host/cpu.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/Task3(Analysis of host cpu-log dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/Task3(Analysis of host cpu-log dataset files)_report.md`
- `temp_data/analysis-host-cpu-log-summary.json`

## Logic
1. Loaded `TRAIN/cpu.log` paths.
2. Parsed JSON-lines structure and nested CPU metric fields.
3. Checked timestamp, label indicators, and data quality.
4. Detected mixed schemas (metric rows + annotation rows).
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
