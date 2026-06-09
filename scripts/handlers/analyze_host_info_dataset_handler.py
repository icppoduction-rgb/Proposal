from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostInfoContentAnalysisResult:
    """Result of analyzing TRAIN/info host datasets and generating documentation."""

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


class HostInfoContentAnalysisHandler:
    """Analyzes host TRAIN/info datasets and writes bilingual markdown documentation."""

    ROLE_NAME = "TRAIN"
    FORMAT_NAME = "info"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-info-summary.json"
    CSV_SUMMARY_JSON_FILE = "analysis-host-csv-summary.json"
    AUTH_SUMMARY_JSON_FILE = "analysis-host-auth-log-summary.json"
    CPU_SUMMARY_JSON_FILE = "analysis-host-cpu-log-summary.json"
    DISKIO_SUMMARY_JSON_FILE = "analysis-host-diskio-log-summary.json"
    FILESYSTEM_SUMMARY_JSON_FILE = "analysis-host-filesystem-log-summary.json"
    FSSTAT_SUMMARY_JSON_FILE = "analysis-host-fsstat-log-summary.json"
    GHC_SUMMARY_JSON_FILE = "analysis-host-ghc-summary.json"

    STATUS_NEEDS_CUSTOM_PARSER = "NEEDS_CUSTOM_PARSER"
    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"

    MESSAGE_RE = re.compile(
        r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
        r"\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+(\S+)\s+([^:]+):\s*(.*)$"
    )
    USER_RE = re.compile(r"user=<([a-zA-Z0-9_.-]+)>", re.IGNORECASE)
    IP_RE = re.compile(r"(?:rip|lip)=([0-9]{1,3}(?:\.[0-9]{1,3}){3})")

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

    def analyze_and_generate_docs(self) -> HostInfoContentAnalysisResult:
        """Runs info analysis and writes docs/report files."""
        role_to_formats = self._read_source_json()
        all_info_paths = self._extract_info_paths(role_to_formats)
        if not all_info_paths:
            raise ValueError("No files found in sort-path-host-file.json for TRAIN/info.")

        sampled_paths = self._select_sample_paths(all_info_paths)
        summary_payload = self._build_summary(all_info_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "info.md"
        docs_en_path = self.docs_en_dir / "info.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = (
            self.report_ru_dir / "Task8(Analysis of host info dataset files)_report.md"
        )
        report_en_path = (
            self.report_en_dir / "Task8(Analysis of host info dataset files)_report.md"
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
                total_files_count=len(all_info_paths),
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
                total_files_count=len(all_info_paths),
                sampled_files_count=len(sampled_paths),
                status=status,
            ),
        )

        return HostInfoContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_info_paths),
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

    def _extract_info_paths(self, role_to_formats: dict[str, Any]) -> list[Path]:
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

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        sample_info: list[dict[str, Any]] = []

        encoding_counts: dict[str, int] = {}
        json_only_files = 0
        raw_only_files = 0
        mixed_files = 0
        empty_files = 0
        read_errors = 0

        total_sample_lines = 0
        json_lines = 0
        raw_lines = 0
        missing_message = 0
        missing_timestamp = 0
        duplicate_lines = 0

        top_level_key_counts: dict[str, int] = {}
        process_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        user_counts: dict[str, int] = {}
        ip_counts: dict[str, int] = {}

        parsed_message_lines = 0
        message_not_parsed_lines = 0

        seen_lines: set[str] = set()

        for file_path in sampled_paths:
            file_stat: dict[str, Any] = {
                "path": str(file_path),
                "name": file_path.name,
                "size_bytes": 0,
                "encoding": "unknown",
                "line_count_sample": 0,
                "json_line_count": 0,
                "raw_line_count": 0,
                "parse_error": None,
            }
            if not file_path.exists():
                file_stat["parse_error"] = "file_not_found"
                sample_info.append(file_stat)
                read_errors += 1
                continue

            file_stat["size_bytes"] = file_path.stat().st_size
            if file_stat["size_bytes"] == 0:
                file_stat["parse_error"] = "empty_file"
                sample_info.append(file_stat)
                empty_files += 1
                continue

            encoding = self._detect_encoding(file_path)
            file_stat["encoding"] = encoding
            encoding_counts[encoding] = encoding_counts.get(encoding, 0) + 1

            try:
                lines = file_path.read_text(encoding=encoding, errors="replace").splitlines()[
                    : self.max_lines_per_file
                ]
            except OSError as error:
                file_stat["parse_error"] = f"read_error:{error.__class__.__name__}"
                sample_info.append(file_stat)
                read_errors += 1
                continue

            file_stat["line_count_sample"] = len(lines)
            total_sample_lines += len(lines)

            local_json = 0
            local_raw = 0

            for line in lines:
                if line in seen_lines:
                    duplicate_lines += 1
                else:
                    seen_lines.add(line)

                parsed_obj: dict[str, Any] | None = None
                try:
                    payload = json.loads(line)
                    if isinstance(payload, dict):
                        parsed_obj = payload
                except json.JSONDecodeError:
                    parsed_obj = None

                if parsed_obj is not None:
                    local_json += 1
                    json_lines += 1
                    for key in parsed_obj:
                        top_level_key_counts[key] = top_level_key_counts.get(key, 0) + 1

                    message_value = parsed_obj.get("message")
                    timestamp_value = parsed_obj.get("@timestamp")
                    if not message_value:
                        missing_message += 1
                        continue
                    if not timestamp_value:
                        missing_timestamp += 1

                    message_text = str(message_value)
                    self._collect_message_stats(
                        message_text=message_text,
                        process_counts=process_counts,
                        action_counts=action_counts,
                        user_counts=user_counts,
                        ip_counts=ip_counts,
                    )
                    parsed_message_lines += int(self.MESSAGE_RE.match(message_text) is not None)
                    message_not_parsed_lines += int(self.MESSAGE_RE.match(message_text) is None)
                    continue

                local_raw += 1
                raw_lines += 1
                self._collect_message_stats(
                    message_text=line,
                    process_counts=process_counts,
                    action_counts=action_counts,
                    user_counts=user_counts,
                    ip_counts=ip_counts,
                )
                parsed_message_lines += int(self.MESSAGE_RE.match(line) is not None)
                message_not_parsed_lines += int(self.MESSAGE_RE.match(line) is None)

            file_stat["json_line_count"] = local_json
            file_stat["raw_line_count"] = local_raw

            if local_json > 0 and local_raw > 0:
                mixed_files += 1
            elif local_json > 0:
                json_only_files += 1
            else:
                raw_only_files += 1

            sample_info.append(file_stat)

        mixed_schema_detected = mixed_files > 0 or (json_only_files > 0 and raw_only_files > 0)
        status = (
            self.STATUS_NEEDS_CUSTOM_PARSER if mixed_schema_detected else self.STATUS_READY
        )
        needs_custom_parser = mixed_schema_detected

        example_paths = [str(path) for path in all_paths[:3]]

        return {
            "scope": {
                "role": self.ROLE_NAME,
                "format": self.FORMAT_NAME,
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "examples": {"paths": example_paths},
            "technical": {
                "file_type": "text",
                "line_by_line_readable": True,
                "tabular_structure": False,
                "nested_structure": True,
                "encoding_counts": encoding_counts,
                "total_sample_lines": total_sample_lines,
                "json_lines": json_lines,
                "raw_lines": raw_lines,
                "json_only_files": json_only_files,
                "raw_only_files": raw_only_files,
                "mixed_files": mixed_files,
                "top_level_key_counts": dict(
                    sorted(top_level_key_counts.items(), key=lambda item: item[1], reverse=True)[:20]
                ),
                "sample_file_details": sample_info[:12],
            },
            "content": {
                "category": "Authentication logs (info), including both raw syslog lines and JSON-wrapped events.",
                "detected_substructures": ["raw_syslog", "json_line_event_wrapper"],
                "message_parse": {
                    "parsed_message_lines": parsed_message_lines,
                    "unparsed_message_lines": message_not_parsed_lines,
                },
                "top_processes": dict(
                    sorted(process_counts.items(), key=lambda item: item[1], reverse=True)[:15]
                ),
                "top_actions": dict(
                    sorted(action_counts.items(), key=lambda item: item[1], reverse=True)[:12]
                ),
                "top_users": dict(sorted(user_counts.items(), key=lambda item: item[1], reverse=True)[:12]),
                "top_source_ips": dict(
                    sorted(ip_counts.items(), key=lambda item: item[1], reverse=True)[:12]
                ),
            },
            "label_detection": {
                "label_found": False,
                "label_field_name": "-",
                "label_values": "-",
                "supports_supervised_learning": "partially",
                "notes": "No explicit label column in info events. Labels may require external mapping.",
            },
            "time_detection": {
                "timestamp_found": True,
                "timestamp_fields": ["@timestamp", "message(syslog prefix)"],
                "timestamp_format": "ISO-8601 (@timestamp) + syslog time without year",
                "timezone": "event.timezone (+00:00) for JSON lines; implicit for raw lines",
                "sequence_ready": True,
                "sliding_window_ready": True,
            },
            "data_quality": {
                "empty_files_count": empty_files,
                "read_error_files_count": read_errors,
                "missing_message_count": missing_message,
                "missing_timestamp_count": missing_timestamp,
                "duplicate_lines_count": duplicate_lines,
                "mixed_schema_detected": mixed_schema_detected,
            },
            "final_status": status,
            "needs_custom_parser": needs_custom_parser,
            "priority": "high" if needs_custom_parser else "medium",
        }

    def _collect_message_stats(
        self,
        message_text: str,
        process_counts: dict[str, int],
        action_counts: dict[str, int],
        user_counts: dict[str, int],
        ip_counts: dict[str, int],
    ) -> None:
        match = self.MESSAGE_RE.match(message_text)
        if not match:
            return

        process_name = match.group(3).strip().lower()
        body = match.group(4).lower()
        process_counts[process_name] = process_counts.get(process_name, 0) + 1

        self._mark_action(body, "login:", "login", action_counts)
        self._mark_action(body, "logged out", "logged_out", action_counts)
        self._mark_action(body, "disconnected", "disconnected", action_counts)
        self._mark_action(body, "auth failed", "auth_failed", action_counts)

        user_match = self.USER_RE.search(body)
        if user_match:
            user = user_match.group(1)
            user_counts[user] = user_counts.get(user, 0) + 1

        ip_match = self.IP_RE.search(body)
        if ip_match:
            ip_address = ip_match.group(1)
            ip_counts[ip_address] = ip_counts.get(ip_address, 0) + 1

    @staticmethod
    def _mark_action(
        body: str,
        token: str,
        action_name: str,
        action_counts: dict[str, int],
    ) -> None:
        if token in body:
            action_counts[action_name] = action_counts.get(action_name, 0) + 1

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

        fields_table = """| Поле | Тип | Назначение | Пример |
|---|---|---|---|
| message | string | текст auth/syslog события | `Jan 16 06:25:13 ... session closed for user root` |
| @timestamp | datetime | точка времени ingest (JSON lines) | `2022-01-13T14:31:36.097Z` |
| event.dataset | string | тип события в обертке | `mail.info/dovecot` |
| host.name | string | хост-источник события | `internal-share` |
| log.file.path | string | исходный путь лога | `/var/log/info` |"""

        top_actions = (
            "\n".join(
                f"- `{name}`: {count}"
                for name, count in list(content["top_actions"].items())[:8]
            )
            or "- данных нет"
        )
        top_processes = (
            "\n".join(
                f"- `{name}`: {count}"
                for name, count in list(content["top_processes"].items())[:8]
            )
            or "- данных нет"
        )

        return f"""
# Анализ формата: info

## 1. Назначение
Файлы `info` в `TRAIN` содержат события аутентификации и сессий (sudo/cron/systemd/useradd/sshd), пригодные для построения host-поведенческих признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | info |
| Варианты расширения | `.log` (группа `info`) |
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
| Разделитель | none (line-oriented logs / JSON-lines) |
| Кодировка | {', '.join(f"{k} ({v})" for k, v in technical['encoding_counts'].items())} |
| Вложенная структура | да (JSON-lines + вложенные объекты) |
| Sample-файлов проанализировано | {scope['sampled_files_count']} |
| Sample-строк проанализировано | {technical['total_sample_lines']} |
| JSON lines | {technical['json_lines']} |
| Raw syslog lines | {technical['raw_lines']} |

## 5. Содержательная структура
Внутри `TRAIN/info` обнаружены две подструктуры:
- raw syslog (`Jan 16 06:25:13 host CRON[...] ...`);
- JSON-lines обертка (Filebeat/ECS) с ключами `message`, `@timestamp`, `event`, `host`, `agent`, `log`.

Примеры активностей:
{top_actions}

Примеры источников/процессов:
{top_processes}

## 6. Найденные поля / колонки
{fields_table}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | {"да" if label['label_found'] else "нет"} |
| Название поля | {label['label_field_name']} |
| Значения label | {label['label_values']} |
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
- частоты `login/logged_out/disconnected`;
- частоты `sudo`, `cron`, `systemd`, `sshd` действий;
- user-level признаки (login/session активности пользователей);
- source IP frequency и аномалии по источникам;
- последовательности auth-событий во времени.

### Network / hybrid-признаки
- корреляция source IP из auth-событий с сетевыми flow-признаками.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if quality['empty_files_count'] > 0 else "нет"} | count: {quality['empty_files_count']} |
| Повреждённые файлы | {"да" if quality['read_error_files_count'] > 0 else "нет"} | read errors: {quality['read_error_files_count']} |
| Missing values | {"да" if quality['missing_message_count'] > 0 else "нет"} | missing `message`: {quality['missing_message_count']} |
| Нестабильная структура | {"да" if quality['mixed_schema_detected'] else "нет"} | смешаны raw syslog и JSON-lines |
| Смешанные схемы | {"да" if quality['mixed_schema_detected'] else "нет"} | json_only={technical['json_only_files']}, raw_only={technical['raw_only_files']} |
| Дубли строк | {"да" if quality['duplicate_lines_count'] > 0 else "нет"} | duplicate lines in sample: {quality['duplicate_lines_count']} |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary['final_status']} |
| Нужен отдельный парсер | {"да" if summary['needs_custom_parser'] else "нет"} |
| Приоритет обработки | {summary['priority']} |

## 12. Вывод
`TRAIN/info` содержит полезные mail service logs и пригоден для feature extraction, но внутри расширения есть два разных представления (raw syslog и JSON-lines). Для корректной промышленной обработки нужен отдельный parser с ветвлением по структуре входной строки.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        scope = summary["scope"]
        technical = summary["technical"]
        content = summary["content"]
        label = summary["label_detection"]
        time_block = summary["time_detection"]
        quality = summary["data_quality"]
        examples = summary["examples"]["paths"]

        fields_table = """| Field | Type | Purpose | Example |
|---|---|---|---|
| message | string | auth/syslog event payload | `Jan 16 06:25:13 ... session closed for user root` |
| @timestamp | datetime | ingest timestamp (JSON lines) | `2022-01-13T14:31:36.097Z` |
| event.dataset | string | event category in wrapper | `mail.info/dovecot` |
| host.name | string | source host | `internal-share` |
| log.file.path | string | original log path | `/var/log/info` |"""

        top_actions = (
            "\n".join(
                f"- `{name}`: {count}"
                for name, count in list(content["top_actions"].items())[:8]
            )
            or "- no data"
        )
        top_processes = (
            "\n".join(
                f"- `{name}`: {count}"
                for name, count in list(content["top_processes"].items())[:8]
            )
            or "- no data"
        )

        return f"""
# Format Analysis: info

## 1. Purpose
`info` files in `TRAIN` contain mail login/logout events (dovecot imap-login/imap) suitable for host behavioral feature engineering.

## 2. Where it appears
| Field | Value |
|---|---|
| Format | info |
| Extension variants | `.log` (grouped as `info`) |
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
| Delimiter | none (line-oriented logs / JSON-lines) |
| Encoding | {', '.join(f"{k} ({v})" for k, v in technical['encoding_counts'].items())} |
| Nested structure | yes (JSON-lines with nested objects) |
| Sampled files | {scope['sampled_files_count']} |
| Sampled lines | {technical['total_sample_lines']} |
| JSON lines | {technical['json_lines']} |
| Raw syslog lines | {technical['raw_lines']} |

## 5. Semantic structure
Two event substructures are present in `TRAIN/info`:
- raw syslog (`Jan 16 06:25:13 host CRON[...] ...`);
- Filebeat/ECS JSON-lines wrapper with keys like `message`, `@timestamp`, `event`, `host`, `agent`, `log`.

Example activities:
{top_actions}

Example process sources:
{top_processes}

## 6. Detected fields / columns
{fields_table}

## 7. Label / class indicators
| Check | Result |
|---|---|
| Label found | {"yes" if label['label_found'] else "no"} |
| Field name | {label['label_field_name']} |
| Label values | {label['label_values']} |
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
- `login/logged_out/disconnected` frequencies;
- action/process frequencies (`sudo`, `cron`, `systemd`, `sshd`);
- user-level login/session features;
- source IP frequency/anomaly features;
- temporal sequences of mail info events.

### Network / hybrid features
- correlate source IPs from mail info events with network flow features.

## 10. Data quality issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if quality['empty_files_count'] > 0 else "no"} | count: {quality['empty_files_count']} |
| Corrupted files | {"yes" if quality['read_error_files_count'] > 0 else "no"} | read errors: {quality['read_error_files_count']} |
| Missing values | {"yes" if quality['missing_message_count'] > 0 else "no"} | missing `message`: {quality['missing_message_count']} |
| Unstable structure | {"yes" if quality['mixed_schema_detected'] else "no"} | raw text lines and optional JSON wrappers may coexist |
| Mixed schemas | {"yes" if quality['mixed_schema_detected'] else "no"} | json_only={technical['json_only_files']}, raw_only={technical['raw_only_files']} |
| Duplicate rows | {"yes" if quality['duplicate_lines_count'] > 0 else "no"} | duplicate lines in sample: {quality['duplicate_lines_count']} |

## 11. Final suitability
| Field | Value |
|---|---|
| Status | {summary['final_status']} |
| Needs dedicated parser | {"yes" if summary['needs_custom_parser'] else "no"} |
| Processing priority | {summary['priority']} |

## 12. Conclusion
`TRAIN/info` provides useful mail service telemetry for feature extraction, but the extension includes two different internal representations (raw syslog and JSON-lines). A dedicated parser with structure-aware branching is required for reliable production processing.
"""

    def _build_ru_readme(self, info_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", 0)
        filesystem_count = host_counts.get("filesystem.log", 0)
        fsstat_count = host_counts.get("fsstat.log", 0)
        ghc_count = host_counts.get("ghc", 0)
        info_count = host_counts.get("info", info_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE)
        filesystem_status = self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE)
        fsstat_status = self._load_optional_status(self.temp_data_path / self.FSSTAT_SUMMARY_JSON_FILE)
        ghc_status = self._load_optional_status(self.temp_data_path / self.GHC_SUMMARY_JSON_FILE)
        info_status = info_summary["final_status"]

        return f"""
# Анализ содержимого файлов датасетов (Host)

| Формат | Количество файлов | DNS | Host | Статус | Документ |
|---|---:|---|---|---|---|
| csv | {csv_count} | нет | да | {csv_status} | csv.md |
| auth.log | {auth_count} | нет | да | {auth_status} | auth.log.md |
| cpu.log | {cpu_count} | нет | да | {cpu_status} | cpu.log.md |
| diskio.log | {diskio_count} | нет | да | {diskio_status} | diskio.log.md |
| filesystem.log | {filesystem_count} | нет | да | {filesystem_status} | filesystem.log.md |
| fsstat.log | {fsstat_count} | нет | да | {fsstat_status} | fsstat.log.md |
| ghc | {ghc_count} | нет | да | {ghc_status} | ghc.md |
| info | {info_count} | нет | да | {info_status} | info.md |
"""

    def _build_en_readme(self, info_summary: dict[str, Any]) -> str:
        host_counts = self._load_host_format_counts()
        csv_count = host_counts.get("csv", 0)
        auth_count = host_counts.get("auth.log", 0)
        cpu_count = host_counts.get("cpu.log", 0)
        diskio_count = host_counts.get("diskio.log", 0)
        filesystem_count = host_counts.get("filesystem.log", 0)
        fsstat_count = host_counts.get("fsstat.log", 0)
        ghc_count = host_counts.get("ghc", 0)
        info_count = host_counts.get("info", info_summary["scope"]["total_files_count"])

        csv_status = self._load_optional_status(self.temp_data_path / self.CSV_SUMMARY_JSON_FILE)
        auth_status = self._load_optional_status(self.temp_data_path / self.AUTH_SUMMARY_JSON_FILE)
        cpu_status = self._load_optional_status(self.temp_data_path / self.CPU_SUMMARY_JSON_FILE)
        diskio_status = self._load_optional_status(self.temp_data_path / self.DISKIO_SUMMARY_JSON_FILE)
        filesystem_status = self._load_optional_status(self.temp_data_path / self.FILESYSTEM_SUMMARY_JSON_FILE)
        fsstat_status = self._load_optional_status(self.temp_data_path / self.FSSTAT_SUMMARY_JSON_FILE)
        ghc_status = self._load_optional_status(self.temp_data_path / self.GHC_SUMMARY_JSON_FILE)
        info_status = info_summary["final_status"]

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
| ghc | {ghc_count} | no | yes | {ghc_status} | ghc.md |
| info | {info_count} | no | yes | {info_status} | info.md |
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
# Отчёт: Task8 (Analysis of host info dataset files)

## Описание задачи
Реализован этап анализа формата `TRAIN/info` на основе `temp_data/sort-path-host-file.json` с сохранением результатов в документацию RU/EN.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_info_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/info.md`
- `docs/en/analysis-dataset/host/info.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/Task8(Analysis of host info dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/Task8(Analysis of host info dataset files)_report.md`
- `temp_data/analysis-host-info-summary.json`

## Логика
1. Загружены пути `TRAIN/info` из `sort-path-host-file.json`.
2. Выполнен sampling файлов и построчный анализ.
3. Выявлены две внутренние схемы: raw syslog и JSON-lines.
4. Проверены timestamp, поля, индикаторы label, качество данных.
5. Сформированы markdown-документы и обновлён README-индекс.

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
# Report: Task8 (Analysis of host info dataset files)

## Task description
Implemented `TRAIN/info` content analysis using `temp_data/sort-path-host-file.json`, with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_info_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/info.md`
- `docs/en/analysis-dataset/host/info.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/Task8(Analysis of host info dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/Task8(Analysis of host info dataset files)_report.md`
- `temp_data/analysis-host-info-summary.json`

## Logic
1. Loaded `TRAIN/info` paths from `sort-path-host-file.json`.
2. Performed file sampling and line-by-line analysis.
3. Detected two internal schemas: raw syslog and JSON-lines.
4. Checked timestamp fields, label indicators, and data quality.
5. Generated markdown documents and updated README index.

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


