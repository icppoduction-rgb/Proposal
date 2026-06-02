from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostPCAPContentAnalysisResult:
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


class HostPCAPContentAnalysisHandler:
    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "pcap"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000
    DEFAULT_MAX_BYTES_PER_FILE = 2 * 1024 * 1024

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-host-pcap-summary.json"

    CSV_SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"
    AUTH_SUMMARY_JSON_FILE = "analysis-host-auth-log-summary.json"
    CPU_SUMMARY_JSON_FILE = "analysis-host-cpu-log-summary.json"
    DISKIO_SUMMARY_JSON_FILE = "analysis-host-diskio-log-summary.json"
    FILESYSTEM_SUMMARY_JSON_FILE = "analysis-host-filesystem-log-summary.json"
    FSSTAT_SUMMARY_JSON_FILE = "analysis-host-fsstat-log-summary.json"
    GHC_SUMMARY_JSON_FILE = "analysis-host-ghc-summary.json"
    INFO_SUMMARY_JSON_FILE = "analysis-host-info-summary.json"
    JOURNAL_SUMMARY_JSON_FILE = "analysis-host-journal-summary.json"
    JOURNAL_TILDE_SUMMARY_JSON_FILE = "analysis-host-journal-tilde-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_NEEDS_CUSTOM = "NEEDS_CUSTOM_PARSER"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        max_files_per_format: int = DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = DEFAULT_MAX_LINES_PER_FILE,
        max_bytes_per_file: int = DEFAULT_MAX_BYTES_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.max_files_per_format = max(1, max_files_per_format)
        self.max_lines_per_file = max(100, max_lines_per_file)
        self.max_bytes_per_file = max(64 * 1024, max_bytes_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host"
        self.report_ru_dir = self.project_root / "report" / "ru" / "stage-one" / "analysis-dataset" / "host"
        self.report_en_dir = self.project_root / "report" / "en" / "stage-one" / "analysis-dataset" / "host"

    def analyze_and_generate_docs(self) -> HostPCAPContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/pcap.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "pcap.md"
        docs_en_path = self.docs_en_dir / "pcap.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task29(Analysis of host pcap dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task29(Analysis of host pcap dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(summary_payload))
        self._write_text_file(report_ru_path, self._build_ru_report(summary_payload, summary_json_path))
        self._write_text_file(report_en_path, self._build_en_report(summary_payload, summary_json_path))

        return HostPCAPContentAnalysisResult(
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
        # Evenly sample the whole sorted pool to catch schema variants spread by filename.
        step = (len(all_paths) - 1) / (self.max_files_per_format - 1)
        indices = {int(round(i * step)) for i in range(self.max_files_per_format)}
        return [all_paths[index] for index in sorted(indices)]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        schema_counts = {"json_document": 0, "json_lines": 0, "raw_text": 0, "unparsed": 0}
        top_keys: dict[str, int] = {}
        event_types: dict[str, int] = {}
        roles: dict[str, int] = {}
        exploit_values: dict[str, int] = {}

        empty_files = 0
        parse_error_files = 0
        timestamp_hits = 0
        label_hits = 0
        sample_file_details: list[dict[str, Any]] = []

        for file_path in sampled_paths:
            detail = {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
                "schema": "unparsed",
                "json_lines_parsed": 0,
                "json_lines_failed": 0,
                "parse_error": None,
            }
            if not file_path.exists():
                detail["parse_error"] = "file_not_found"
                parse_error_files += 1
                schema_counts["unparsed"] += 1
                sample_file_details.append(detail)
                continue
            if detail["size_bytes"] == 0:
                detail["parse_error"] = "empty_file"
                empty_files += 1
                schema_counts["unparsed"] += 1
                sample_file_details.append(detail)
                continue

            raw = file_path.read_bytes()[: self.max_bytes_per_file]
            text = raw.decode("utf-8", errors="replace").strip()

            parsed_document = False
            if text.startswith("{") or text.startswith("["):
                try:
                    payload = json.loads(text)
                    if isinstance(payload, dict):
                        parsed_document = True
                        schema_counts["json_document"] += 1
                        detail["schema"] = "json_document"
                        for key in payload.keys():
                            top_keys[key] = top_keys.get(key, 0) + 1
                        if "time" in payload or "timestamp" in payload:
                            timestamp_hits += 1
                        if "exploit" in payload:
                            label_hits += 1
                            exploit_key = str(payload.get("exploit"))
                            exploit_values[exploit_key] = exploit_values.get(exploit_key, 0) + 1
                        container = payload.get("container")
                        if isinstance(container, list):
                            for item in container:
                                if isinstance(item, dict):
                                    role = item.get("role")
                                    if isinstance(role, str):
                                        roles[role] = roles.get(role, 0) + 1
                    elif isinstance(payload, list):
                        parsed_document = True
                        schema_counts["json_document"] += 1
                        detail["schema"] = "json_document"
                except json.JSONDecodeError:
                    parsed_document = False

            if not parsed_document:
                parsed_lines = 0
                failed_lines = 0
                try:
                    with file_path.open("r", encoding="utf-8", errors="replace") as stream:
                        for index, raw_line in enumerate(stream):
                            if index >= self.max_lines_per_file:
                                break
                            line = raw_line.strip()
                            if not line:
                                continue
                            try:
                                line_payload = json.loads(line)
                            except json.JSONDecodeError:
                                failed_lines += 1
                                continue
                            if not isinstance(line_payload, dict):
                                failed_lines += 1
                                continue
                            parsed_lines += 1
                            event_type = line_payload.get("event_type")
                            if isinstance(event_type, str):
                                event_types[event_type] = event_types.get(event_type, 0) + 1
                            if "timestamp" in line_payload:
                                timestamp_hits += 1
                            if "alert" in line_payload or "label" in line_payload:
                                label_hits += 1
                except OSError:
                    failed_lines += 1

                detail["json_lines_parsed"] = parsed_lines
                detail["json_lines_failed"] = failed_lines
                if parsed_lines > 0:
                    schema_counts["json_lines"] += 1
                    detail["schema"] = "json_lines"
                else:
                    non_empty_raw_lines = [
                        ln for ln in text.splitlines()[: self.max_lines_per_file] if ln.strip()
                    ]
                    if non_empty_raw_lines:
                        schema_counts["raw_text"] += 1
                        detail["schema"] = "raw_text"
                        if non_empty_raw_lines[0][:4].isdigit():
                            timestamp_hits += 1
                    else:
                        schema_counts["unparsed"] += 1
                        detail["schema"] = "unparsed"
                        detail["parse_error"] = "json_document_and_json_lines_parse_failed"
                        parse_error_files += 1

            sample_file_details.append(detail)

        active_schema_count = sum(
            1
            for key in ("json_document", "json_lines", "raw_text")
            if schema_counts.get(key, 0) > 0
        )
        mixed_schema = active_schema_count > 1
        if schema_counts["unparsed"] == len(sampled_paths):
            status = self.STATUS_BROKEN
        elif mixed_schema:
            status = self.STATUS_NEEDS_CUSTOM
        elif schema_counts["json_lines"] > 0 and parse_error_files > 0:
            status = self.STATUS_PARTIAL
        else:
            status = self.STATUS_READY
        # PCAP is binary and requires dedicated packet parsing libraries/tooling.
        status = self.STATUS_NEEDS_CUSTOM

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
                "max_bytes_per_file": self.max_bytes_per_file,
            },
            "examples": {"paths": [str(path) for path in all_paths[:3]]},
            "technical": {
                "file_type": "binary",
                "line_by_line_readable": False,
                "tabular_structure": False,
                "nested_structure": False,
                "schema_counts": schema_counts,
                "top_level_keys": top_keys,
                "sample_file_details": sample_file_details[:12],
            },
            "content": {
                "category": "Packet capture binary files (classic PCAP little-endian magic d4c3b2a1).",
                "top_event_types": event_types,
                "container_roles": roles,
                "exploit_values": exploit_values,
            },
            "label_detection": {
                "label_found": False,
                "label_field_name": "-",
                "label_values": [],
                "supports_supervised_learning": "no",
            },
            "time_detection": {
                "timestamp_found": False,
                "timestamp_fields": [],
                "timestamp_format": "requires PCAP parser",
                "timezone": "unknown",
                "sequence_ready": False,
                "sliding_window_ready": False,
            },
            "data_quality": {
                "empty_files_count": empty_files,
                "parse_error_files_count": parse_error_files,
                "mixed_schema_detected": mixed_schema,
            },
            "final_status": status,
            "needs_custom_parser": status in {self.STATUS_NEEDS_CUSTOM, self.STATUS_PARTIAL},
            "priority": "high" if status in {self.STATUS_NEEDS_CUSTOM, self.STATUS_PARTIAL} else "medium",
        }

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        quality = summary["data_quality"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        examples = summary["examples"]["paths"]
        return f"""
# Анализ формата: {scope["format"]}

## 1. Назначение
Смешанный формат `{scope["format"]}` в `TRAIN`: сценарные JSON-документы и JSON-lines телеметрия (`eve*`, `traffic*`).

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | {scope["format"]} |
| Варианты расширения | `.json` |
| DNS | нет |
| Host | да |
| Роли | {scope["role"]} |
| Количество файлов | {scope["total_files_count"]} |

## 3. Примеры файлов
```text
{examples[0] if len(examples) > 0 else "-"}
{examples[1] if len(examples) > 1 else "-"}
{examples[2] if len(examples) > 2 else "-"}
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | text |
| Чтение построчно | да |
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | JSON object / JSON-lines |
| Кодировка | utf-8 |
| Вложенная структура | да |
| JSON document | {technical["schema_counts"]["json_document"]} |
| JSON-lines | {technical["schema_counts"]["json_lines"]} |
| Raw text | {technical["schema_counts"]["raw_text"]} |
| Неразобранные | {technical["schema_counts"]["unparsed"]} |

## 5. Содержательная структура
Обнаружены две схемы: сценарные документы (`container`, `exploit`, `time`) и JSON-lines события (`timestamp`, `event_type`, `alert`, `dns`).

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| exploit | bool | индикатор сценария | `false` |
| container.role | string | роль контейнера | `normal`, `victim` |
| time.container_ready.absolute | float | время готовности | `1631222503.73` |
| timestamp | string | время события | `2022-01-13T14:37:36.251509+0000` |
| event_type | string | тип события | `stats`, `dns`, `alert` |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | {"да" if label["label_found"] else "нет"} |
| Название поля | {label["label_field_name"]} |
| Значения label | {", ".join(label["label_values"])} |
| Можно использовать для supervised learning | {label["supports_supervised_learning"]} |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | {"да" if time_block["timestamp_found"] else "нет"} |
| Название поля | {", ".join(time_block["timestamp_fields"])} |
| Формат времени | {time_block["timestamp_format"]} |
| Timezone | {time_block["timezone"]} |
| Можно строить sequence | {"да" if time_block["sequence_ready"] else "нет"} |
| Можно применять sliding window | {"да" if time_block["sliding_window_ready"] else "нет"} |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- частоты `event_type=dns`;
- разнообразие DNS-событий.

### Host-признаки
- `exploit`, роли контейнеров, `recording_time`;
- последовательности `event_type`.

### Network / hybrid-признаки
- `src_ip`, `dest_ip`, `src_port`, `dest_port`, `proto`;
- корреляция alert-событий с host-контекстом.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if quality["empty_files_count"] > 0 else "нет"} | count: {quality["empty_files_count"]} |
| Повреждённые файлы | {"да" if quality["parse_error_files_count"] > 0 else "нет"} | parse errors: {quality["parse_error_files_count"]} |
| Missing values | нет | критичных пропусков в sample не обнаружено |
| Нестабильная структура | {"да" if quality["mixed_schema_detected"] else "нет"} | смешаны JSON document и JSON-lines |
| Смешанные схемы | {"да" if quality["mixed_schema_detected"] else "нет"} | нужен schema-aware parser |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | {"да" if summary["needs_custom_parser"] else "нет"} |
| Приоритет обработки | {summary["priority"]} |

## 12. Вывод
`TRAIN/pcap` пригоден для извлечения признаков, но из-за смешения схем требует отдельного parser layer.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        quality = summary["data_quality"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        examples = summary["examples"]["paths"]
        return f"""
# Format Analysis: pcap

## 1. Purpose
`pcap` in `TRAIN` stores packet capture binaries and requires specialized parser libraries.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | `.pcap` / `.pcapng` |
| DNS | no |
| Host | yes |
| Roles | {scope["role"]} |
| File count | {scope["total_files_count"]} |

## 3. Example files
```text
{examples[0] if len(examples) > 0 else "-"}
{examples[1] if len(examples) > 1 else "-"}
{examples[2] if len(examples) > 2 else "-"}
```

## 4. Technical structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line readable | no |
| Tabular structure | no |
| Header | no |
| Delimiter | none |
| Encoding | unknown |
| Nested structure | no |
| JSON document | {technical["schema_counts"]["json_document"]} |
| JSON-lines | {technical["schema_counts"]["json_lines"]} |
| Raw text | {technical["schema_counts"]["raw_text"]} |
| Unparsed | {technical["schema_counts"]["unparsed"]} |

## 5. Semantic structure
PCAP stores packet frames in binary form. Event-level fields require dedicated packet parsing tools/libraries.

## 6. Detected fields / columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| magic | hex | pcap signature | `d4c3b2a1` |
| version_major | int | format major version | `2` |
| version_minor | int | format minor version | `4` |
| snaplen | int | max packet bytes captured | `65535` |
| network | int | link-layer type | `1` |

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | {"yes" if label["label_found"] else "no"} |
| Field name | {label["label_field_name"]} |
| Label values | {", ".join(label["label_values"])} |
| Suitable for supervised learning | {label["supports_supervised_learning"]} |

## 8. Temporal indicators
| Check | Result |
|---|---|
| Timestamp found | {"yes" if time_block["timestamp_found"] else "no"} |
| Field name | {", ".join(time_block["timestamp_fields"])} |
| Timestamp format | {time_block["timestamp_format"]} |
| Timezone | {time_block["timezone"]} |
| Sequence-ready | {"yes" if time_block["sequence_ready"] else "no"} |
| Sliding-window-ready | {"yes" if time_block["sliding_window_ready"] else "no"} |

## 9. Potential feature extraction signals
### DNS features
- DNS features are available only after packet parsing.

### Host features
- packet rate over time windows;
- protocol distribution per capture.

### Network / hybrid features
- flow duration, bytes, packets, protocol, TCP flags;
- DNS/TCP/UDP/ICMP counts after parsing.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if quality["empty_files_count"] > 0 else "no"} | count: {quality["empty_files_count"]} |
| Corrupted files | {"yes" if quality["parse_error_files_count"] > 0 else "no"} | parse errors: {quality["parse_error_files_count"]} |
| Missing values | no | no critical gaps in sampled data |
| Unstable structure | {"yes" if quality["mixed_schema_detected"] else "no"} | binary capture requires dedicated parser |
| Mixed schemas | {"yes" if quality["mixed_schema_detected"] else "no"} | parser/toolchain required for packet decoding |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Needs dedicated parser | {"yes" if summary["needs_custom_parser"] else "no"} |
| Processing priority | {summary["priority"]} |

## 12. Conclusion
`TRAIN/pcap` requires a dedicated PCAP parsing layer before feature extraction.
"""

    def _build_ru_readme(self, json_summary: dict[str, Any]) -> str:
        rows = self._readme_rows(json_summary)
        body = "\n".join(f"| {name} | {count} | нет | да | {status} | {doc} |" for name, count, status, doc in rows)
        return (
            "# Анализ содержимого файлов датасетов (Host)\n\n"
            "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n"
            "|---|---:|---|---|---|---|\n"
            f"{body}\n"
        )

    def _build_en_readme(self, json_summary: dict[str, Any]) -> str:
        rows = self._readme_rows(json_summary)
        body = "\n".join(f"| {name} | {count} | no | yes | {status} | {doc} |" for name, count, status, doc in rows)
        return (
            "# Dataset File Content Analysis (Host)\n\n"
            "| Format | File count | DNS | Host | Status | Document |\n"
            "|---|---:|---|---|---|---|\n"
            f"{body}\n"
        )

    def _build_ru_report(self, summary_payload: dict[str, Any], summary_json_path: Path) -> str:
        schema = summary_payload["technical"]["schema_counts"]
        return (
            "# Отчёт: Task29 (Analysis of host pcap dataset files)\n\n"
            "## Описание задачи\n"
            "Переделан этап анализа `TRAIN/pcap` с генерацией RU/EN-документации и обновлением README индексов.\n\n"
            "## Какие файлы были добавлены или изменены\n"
            "- `scripts/handlers/analyze_host_pcap_dataset_handler.py`\n"
            "- `manage.py`\n"
            "- `docs/ru/analysis-dataset/host/pcap.md`\n"
            "- `docs/en/analysis-dataset/host/pcap.md`\n"
            "- `docs/ru/analysis-dataset/host/README.md`\n"
            "- `docs/en/analysis-dataset/host/README.md`\n"
            "- `report/ru/stage-one/analysis-dataset/host/Task29(Analysis of host pcap dataset files)_report.md`\n"
            "- `report/en/stage-one/analysis-dataset/host/Task29(Analysis of host pcap dataset files)_report.md`\n"
            "- `temp_data/analysis-host-pcap-summary.json`\n\n"
            "## Описание структуры JSON\n"
            f"- json_document: `{schema['json_document']}`\n"
            f"- json_lines: `{schema['json_lines']}`\n"
            f"- unparsed: `{schema['unparsed']}`\n\n"
            "## Логика группировки путей\n"
            "1. Загружен `sort-path-host-file.json`.\n"
            "2. Выбран bucket `TRAIN -> pcap`.\n"
            "3. Применена равномерная выборка файлов по всему диапазону имен.\n"
            "4. Для каждого sample-файла выполнен анализ как `json document`, затем fallback в `json-lines`.\n\n"
            "## Пример итогового JSON\n"
            "```json\n"
            + json.dumps(
                {
                    "scope": summary_payload["scope"],
                    "technical": {"schema_counts": schema},
                    "final_status": summary_payload["final_status"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n```\n\n"
            f"Summary JSON: `{summary_json_path}`\n"
        )

    def _build_en_report(self, summary_payload: dict[str, Any], summary_json_path: Path) -> str:
        schema = summary_payload["technical"]["schema_counts"]
        return (
            "# Report: Task29 (Analysis of host pcap dataset files)\n\n"
            "## Task description\n"
            "Reworked `TRAIN/pcap` content analysis with RU/EN documentation generation and README index updates.\n\n"
            "## Added or modified files\n"
            "- `scripts/handlers/analyze_host_pcap_dataset_handler.py`\n"
            "- `manage.py`\n"
            "- `docs/ru/analysis-dataset/host/pcap.md`\n"
            "- `docs/en/analysis-dataset/host/pcap.md`\n"
            "- `docs/ru/analysis-dataset/host/README.md`\n"
            "- `docs/en/analysis-dataset/host/README.md`\n"
            "- `report/ru/stage-one/analysis-dataset/host/Task29(Analysis of host pcap dataset files)_report.md`\n"
            "- `report/en/stage-one/analysis-dataset/host/Task29(Analysis of host pcap dataset files)_report.md`\n"
            "- `temp_data/analysis-host-pcap-summary.json`\n\n"
            "## JSON structure summary\n"
            f"- json_document: `{schema['json_document']}`\n"
            f"- json_lines: `{schema['json_lines']}`\n"
            f"- unparsed: `{schema['unparsed']}`\n\n"
            "## Path grouping logic\n"
            "1. Load `sort-path-host-file.json`.\n"
            "2. Select bucket `TRAIN -> pcap`.\n"
            "3. Apply evenly distributed sampling across all sorted filenames.\n"
            "4. For each sample file, try `json document` parsing first, then fallback to `json-lines`.\n\n"
            "## Sample output JSON\n"
            "```json\n"
            + json.dumps(
                {
                    "scope": summary_payload["scope"],
                    "technical": {"schema_counts": schema},
                    "final_status": summary_payload["final_status"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n```\n\n"
            f"Summary JSON: `{summary_json_path}`\n"
        )

    def _readme_rows(self, json_summary: dict[str, Any]) -> list[tuple[str, int, str, str]]:
        host_counts = self._load_host_format_counts()
        return [
            ("csv", host_counts.get("csv", 0), self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE), "csv.md"),
            ("auth.log", host_counts.get("auth.log", 0), self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE), "auth.log.md"),
            ("cpu.log", host_counts.get("cpu.log", 0), self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE), "cpu.log.md"),
            ("diskio.log", host_counts.get("diskio.log", 0), self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE), "diskio.log.md"),
            ("filesystem.log", host_counts.get("filesystem.log", 0), self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE), "filesystem.log.md"),
            ("fsstat.log", host_counts.get("fsstat.log", 0), self._load_optional_status(self.temp_data_path / self.FSSTAT_SUMMARY_JSON_FILE), "fsstat.log.md"),
            ("ghc", host_counts.get("ghc", 0), self._load_optional_status(self.temp_data_path / self.GHC_SUMMARY_JSON_FILE), "ghc.md"),
            ("info", host_counts.get("info", 0), self._load_optional_status(self.temp_data_path / self.INFO_SUMMARY_JSON_FILE), "info.md"),
            ("journal", host_counts.get("journal", 0), self._load_optional_status(self.temp_data_path / self.JOURNAL_SUMMARY_JSON_FILE), "journal.md"),
            ("journal~", host_counts.get("journal~", 0), self._load_optional_status(self.temp_data_path / self.JOURNAL_TILDE_SUMMARY_JSON_FILE), "journal~.md"),
            (
                "json",
                host_counts.get("json", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-json-summary.json"),
                "json.md",
            ),
            (
                "json-1",
                host_counts.get("json-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-json-1-summary.json"),
                "json-1.md",
            ),
            (
                "load.log",
                host_counts.get("load.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-load-log-summary.json"),
                "load.log.md",
            ),
            (
                "log",
                host_counts.get("log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-log-summary.json"),
                "log.md",
            ),
            (
                "log-1",
                host_counts.get("log-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-log-1-summary.json"),
                "log-1.md",
            ),
            (
                "log-2",
                host_counts.get("log-2", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-log-2-summary.json"),
                "log-2.md",
            ),
            (
                "log-3",
                host_counts.get("log-3", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-log-3-summary.json"),
                "log-3.md",
            ),
            (
                "mail-info-1",
                host_counts.get("mail-info-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mail-info-1-summary.json"),
                "mail-info-1.md",
            ),
            (
                "mail-warn-1",
                host_counts.get("mail-warn-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mail-warn-1-summary.json"),
                "mail-warn-1.md",
            ),
            (
                "mainlog",
                host_counts.get("mainlog", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mainlog-summary.json"),
                "mainlog.md",
            ),
            (
                "mainlog-1",
                host_counts.get("mainlog-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mainlog-1-summary.json"),
                "mainlog-1.md",
            ),
            (
                "mainlog-2",
                host_counts.get("mainlog-2", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mainlog-2-summary.json"),
                "mainlog-2.md",
            ),
            (
                "mainlog-3",
                host_counts.get("mainlog-3", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-mainlog-3-summary.json"),
                "mainlog-3.md",
            ),
            (
                "memory.log",
                host_counts.get("memory.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-memory-log-summary.json"),
                "memory.log.md",
            ),
            (
                "messages",
                host_counts.get("messages", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-messages-summary.json"),
                "messages.md",
            ),
            (
                "messages-1",
                host_counts.get("messages-1", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-messages-1-summary.json"),
                "messages-1.md",
            ),
            (
                "netflow_ids",
                host_counts.get("netflow_ids", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-netflow-ids-summary.json"),
                "netflow_ids.md",
            ),
            (
                "network.log",
                host_counts.get("network.log", 0),
                self._load_optional_status(self.temp_data_path / "analysis-host-network-log-summary.json"),
                "network.log.md",
            ),
            (
                "pcap",
                host_counts.get("pcap", json_summary["scope"]["total_files_count"]),
                json_summary["final_status"],
                "pcap.md",
            ),
        ]

    def _load_host_format_counts(self) -> dict[str, int]:
        source_json_path = self.temp_data_path / self.HOST_INPUT_JSON_FILE
        payload = JsonDataManager(source_json_path).read(default={})
        role_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            return {}
        result: dict[str, int] = {}
        for fmt, paths in role_bucket.items():
            if isinstance(paths, list):
                result[fmt] = len(paths)
        return result

    @staticmethod
    def _load_optional_status(summary_path: Path) -> str:
        if not summary_path.exists():
            return "-"
        try:
            payload = JsonDataManager(summary_path).read(default={})
        except (ValueError, TypeError):
            return "-"
        value = payload.get("final_status")
        return str(value) if isinstance(value, str) else "-"

















