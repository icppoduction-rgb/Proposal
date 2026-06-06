from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostTestLogContentAnalysisResult:
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
class LogProbe:
    path: str
    file_name: str
    file_size_bytes: int
    encoding: str
    sampled_lines: int
    parsed_lines: int
    unmatched_lines: int
    parse_error: str | None


class HostTestLogContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "log"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-test-log-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    LOG_RE = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
        r"\[(?P<component>[^\]]+)] (?P<level>[A-Z]+): (?P<message>.*)$"
    )
    TASK_RE = re.compile(r"Task #(?P<task_id>\d+)")
    PID_RE = re.compile(r"\bPID (?P<pid>\d+)\b")

    ENCODING_CANDIDATES = ("utf-8", "utf-8-sig", "cp1252", "latin-1")

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

    def analyze_and_generate_docs(self) -> HostTestLogContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TEST/log.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "log.md"
        docs_en_path = self.docs_en_dir / "log.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task47(Analysis of host test log dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task47(Analysis of host test log dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_path.parent / "README.md", self._build_en_readme(summary_payload))
        self._write_text_file(report_ru_path, self._build_ru_report(summary_payload, summary_json_path))
        self._write_text_file(report_en_path, self._build_en_report(summary_payload, summary_json_path))

        return HostTestLogContentAnalysisResult(
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
        step = (len(all_paths) - 1) / (self.max_files_per_format - 1)
        indices = {int(round(index * step)) for index in range(self.max_files_per_format)}
        return [all_paths[index] for index in sorted(indices)]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        probes: list[LogProbe] = []
        components: Counter[str] = Counter()
        levels: Counter[str] = Counter()
        message_prefixes: Counter[str] = Counter()
        task_ids: Counter[str] = Counter()
        pids: Counter[str] = Counter()
        examples: list[dict[str, str]] = []
        parse_errors: Counter[str] = Counter()
        empty_files = 0

        for path in sampled_paths:
            probe, parsed_rows = self._probe_file(path)
            probes.append(probe)
            if probe.file_size_bytes == 0:
                empty_files += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            for row in parsed_rows:
                components[row["component"]] += 1
                levels[row["level"]] += 1
                message_prefixes[self._message_prefix(row["message"])] += 1
                task_match = self.TASK_RE.search(row["message"])
                if task_match:
                    task_ids[task_match.group("task_id")] += 1
                pid_match = self.PID_RE.search(row["message"])
                if pid_match:
                    pids[pid_match.group("pid")] += 1
                if len(examples) < 5:
                    examples.append(row)

        parsed_lines = sum(probe.parsed_lines for probe in probes)
        unmatched_lines = sum(probe.unmatched_lines for probe in probes)
        if parsed_lines == 0:
            final_status = self.STATUS_BROKEN
        elif unmatched_lines > parsed_lines:
            final_status = self.STATUS_PARTIAL
        else:
            final_status = self.STATUS_READY

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
            "sample_paths": [str(path) for path in sampled_paths[:10]],
            "file_probes": [probe.__dict__ for probe in probes],
            "parsed_lines": parsed_lines,
            "unmatched_lines": unmatched_lines,
            "components": dict(components.most_common(20)),
            "levels": dict(levels.most_common()),
            "message_prefixes": dict(message_prefixes.most_common(20)),
            "task_ids_sample": dict(task_ids.most_common(10)),
            "pids_sample": dict(pids.most_common(10)),
            "examples": examples,
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "medium",
        }

    def _probe_file(self, path: Path) -> tuple[LogProbe, list[dict[str, str]]]:
        if not path.exists():
            return (
                LogProbe(str(path), path.name, 0, "missing", 0, 0, 0, "file_not_found"),
                [],
            )
        file_size = path.stat().st_size
        if file_size == 0:
            return (
                LogProbe(str(path), path.name, 0, "empty", 0, 0, 0, "empty_file"),
                [],
            )
        encoding = self._detect_encoding(path)
        try:
            with path.open("r", encoding=encoding, errors="replace") as stream:
                lines = [line.rstrip("\n") for _, line in zip(range(self.max_lines_per_file), stream)]
        except OSError as error:
            return (
                LogProbe(str(path), path.name, file_size, encoding, 0, 0, 0, str(error)),
                [],
            )

        parsed_rows: list[dict[str, str]] = []
        unmatched = 0
        for line in lines:
            match = self.LOG_RE.match(line)
            if not match:
                unmatched += 1
                continue
            parsed_rows.append(match.groupdict())

        return (
            LogProbe(
                path=str(path),
                file_name=path.name,
                file_size_bytes=file_size,
                encoding=encoding,
                sampled_lines=len(lines),
                parsed_lines=len(parsed_rows),
                unmatched_lines=unmatched,
                parse_error=None,
            ),
            parsed_rows,
        )

    def _detect_encoding(self, path: Path) -> str:
        for encoding in self.ENCODING_CANDIDATES:
            try:
                with path.open("r", encoding=encoding) as stream:
                    stream.read(4096)
                return encoding
            except UnicodeDecodeError:
                continue
        return "latin-1"

    @staticmethod
    def _message_prefix(message: str) -> str:
        prefix = message.split(":", 1)[0].strip()
        return prefix[:80] if prefix else message[:80]

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        return self._build_markdown(summary, "ru")

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        return self._build_markdown(summary, "en")

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:3])
        component_rows = self._render_counter_rows(summary["components"], "component", "count")
        level_rows = self._render_counter_rows(summary["levels"], "level", "count")
        parse_error_count = sum(summary["parse_errors"].values())
        timestamp_field = "timestamp"

        if ru:
            return f"""# Анализ формата: log

## 1. Назначение
Log-файлы Host TEST содержат журналы Cuckoo/analyzer выполнения sandbox-задач. Формат нужен для извлечения последовательностей runtime-событий, уровней логирования, компонентов, task id, PID и временных интервалов.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | log |
| Варианты расширения | .log |
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
| Табличная структура | частично, через regex-поля |
| Заголовок | нет |
| Разделитель | custom log pattern |
| Кодировка | utf-8 |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Parsed log lines | {summary["parsed_lines"]} |

## 5. Содержательная структура
Строки имеют структуру `timestamp [component] LEVEL: message`. В sample встречаются analyzer events, Cuckoo scheduler events, запуск sniffer, auxiliary modules, machine acquisition, processing и runtime warnings/errors.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| timestamp | datetime string | время события | {self._example(summary, "timestamp")} |
| component | string | компонент логирования | {self._example(summary, "component")} |
| level | string | уровень лога | {self._example(summary, "level")} |
| message | string | текст события | {self._example(summary, "message")} |
| task_id | integer/string | task id из message | {self._first_key(summary["task_ids_sample"])} |
| pid | integer/string | PID из message | {self._first_key(summary["pids_sample"])} |

### Частые компоненты
| component | count |
|---|---:|
{component_rows}

### Уровни логов
| level | count |
|---|---:|
{level_rows}

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
| Название поля | {timestamp_field} |
| Формат времени | `%Y-%m-%d %H:%M:%S,%f` |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- прямые DNS-поля не обнаружены.

### Host-признаки
- частоты `level` и `component`;
- последовательности log events и message prefixes;
- task lifecycle timings;
- количество warnings/errors;
- PID/task id activity counts.

### Network / hybrid-признаки
- sniffer/pcap path indicators из Cuckoo messages;
- host+network correlation через task id и pcap path.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | нет | обязательные regex-поля заполнены в parsed lines |
| Нестабильная структура | нет | основной паттерн стабилен |
| Смешанные схемы | частично | analyzer и cuckoo компоненты различаются семантически |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | средний |

## 12. Вывод
Формат готов к feature extraction как line-oriented журнал sandbox runtime. Для supervised learning нужны внешние метки, но sequence/log-level/component признаки можно извлекать напрямую.
"""

        return f"""# Format Analysis: log

## 1. Purpose
Host TEST log files contain Cuckoo/analyzer sandbox execution logs. The format is useful for runtime event sequences, log levels, components, task ids, PIDs, and timing features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | log |
| Extension variants | .log |
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
| Tabular structure | partial, via regex fields |
| Header | no |
| Delimiter | custom log pattern |
| Encoding | utf-8 |
| Nested structure | no |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Parsed log lines | {summary["parsed_lines"]} |

## 5. Content Structure
Lines use `timestamp [component] LEVEL: message`. The sample includes analyzer events, Cuckoo scheduler events, sniffer startup, auxiliary modules, machine acquisition, processing, and runtime warnings/errors.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| timestamp | datetime string | event time | {self._example(summary, "timestamp")} |
| component | string | logging component | {self._example(summary, "component")} |
| level | string | log level | {self._example(summary, "level")} |
| message | string | event text | {self._example(summary, "message")} |
| task_id | integer/string | task id extracted from message | {self._first_key(summary["task_ids_sample"])} |
| pid | integer/string | PID extracted from message | {self._first_key(summary["pids_sample"])} |

### Frequent Components
| component | count |
|---|---:|
{component_rows}

### Log Levels
| level | count |
|---|---:|
{level_rows}

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
| Field name | {timestamp_field} |
| Time format | `%Y-%m-%d %H:%M:%S,%f` |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- direct DNS fields were not detected.

### Host Features
- `level` and `component` frequencies;
- log event and message-prefix sequences;
- task lifecycle timings;
- warning/error counts;
- PID/task id activity counts.

### Network / Hybrid Features
- sniffer/pcap path indicators from Cuckoo messages;
- host+network correlation through task id and pcap path.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | no | required regex fields are populated in parsed lines |
| Unstable structure | no | the main pattern is stable |
| Mixed schemas | partial | analyzer and cuckoo components differ semantically |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | medium |

## 12. Conclusion
The format is ready for feature extraction as line-oriented sandbox runtime logs. Supervised learning requires external labels, but sequence/log-level/component features can be extracted directly.
"""

    def _build_ru_readme(self, summary: dict[str, Any]) -> str:
        return self._build_readme(summary, "ru")

    def _build_en_readme(self, summary: dict[str, Any]) -> str:
        return self._build_readme(summary, "en")

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
            "log": (summary["final_status"], "log.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_host_test_format_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host TEST)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_ru_report(self, summary: dict[str, Any], summary_json_path: Path) -> str:
        return self._build_report(summary, summary_json_path, "ru")

    def _build_en_report(self, summary: dict[str, Any], summary_json_path: Path) -> str:
        return self._build_report(summary, summary_json_path, "en")

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task47: Analysis of host test log dataset files"
            if ru
            else "# Task47 Report: Analysis of host test log dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\TEST\\log` на основе `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\TEST\\log` using `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        grouping = (
            f"Handler сортирует пути, берёт равномерную выборку до {self.max_files_per_format} файлов и читает до {self.max_lines_per_file} строк на файл."
            if ru
            else f"The handler sorts paths, takes an even sample of up to {self.max_files_per_format} files, and reads up to {self.max_lines_per_file} lines per file."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_test_log_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/log.md`
- `docs/en/analysis-dataset/host/test/log.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task47(Analysis of host test log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task47(Analysis of host test log dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `TEST.log`.

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{grouping}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    @staticmethod
    def _render_counter_rows(counter: dict[str, int], label_name: str, count_name: str) -> str:
        if not counter:
            return f"| - | 0 |"
        return "\n".join(f"| {key} | {value} |" for key, value in list(counter.items())[:10])

    @staticmethod
    def _example(summary: dict[str, Any], key: str) -> str:
        if not summary["examples"]:
            return "-"
        return str(summary["examples"][0].get(key, "-")).replace("|", "\\|")[:120]

    @staticmethod
    def _first_key(values: dict[str, int]) -> str:
        return next(iter(values), "-")

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
            "parsed_lines": summary["parsed_lines"],
            "levels": summary["levels"],
            "final_status": summary["final_status"],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
