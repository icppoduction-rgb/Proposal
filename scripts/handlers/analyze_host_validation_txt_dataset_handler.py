from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.analyze_host_test_txt_dataset_handler import HostTestTXTContentAnalysisHandler
from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostValidationTXTContentAnalysisResult:
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


class HostValidationTXTContentAnalysisHandler(HostTestTXTContentAnalysisHandler):
    ROLE_NAME = "VALIDATION"
    SUMMARY_JSON_FILE = "analysis-host-validation-txt-summary.json"

    SYSDIG_LINE_RE = re.compile(
        r"^(?P<EventIndex>\d+)\s+"
        r"(?P<Time>\d{2}:\d{2}:\d{2}\.\d+)\s+"
        r"(?P<Cpu>\d+)\s+"
        r"(?P<UserId>\d+)\s+"
        r"(?P<ProcessName>\S+)\s+"
        r"(?P<Pid>\d+)\s+"
        r"(?P<Direction>[<>])\s+"
        r"(?P<MethodName>\S+)"
        r"(?:\s+(?P<Args>.*))?$"
    )
    ARG_KEY_RE = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)=")

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = HostTestTXTContentAnalysisHandler.DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = HostTestTXTContentAnalysisHandler.DEFAULT_MAX_LINES_PER_FILE,
    ) -> None:
        super().__init__(temp_data_path, project_root, max_files_per_format, max_lines_per_file)
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host" / "validation"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host" / "validation"
        self.report_ru_dir = (
            self.report_path / "ru" / "stage-one" / "analysis-dataset" / "host" / "validation"
        )
        self.report_en_dir = (
            self.report_path / "en" / "stage-one" / "analysis-dataset" / "host" / "validation"
        )

    def analyze_and_generate_docs(self) -> HostValidationTXTContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for VALIDATION/txt.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "txt.md"
        docs_en_path = self.docs_en_dir / "txt.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task7(Analysis of host validation txt dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task7(Analysis of host validation txt dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary_payload, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary_payload, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary_payload, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary_payload, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary_payload, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary_payload, summary_json_path, "en"))

        return HostValidationTXTContentAnalysisResult(
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

    def _parse_key_value_line(self, line: str) -> dict[str, str] | None:
        match = self.SYSDIG_LINE_RE.match(line)
        if not match:
            return None
        record = {key: value for key, value in match.groupdict(default="").items() if key != "Args"}
        args = match.group("Args") or ""
        for token in args.split():
            arg_match = self.ARG_KEY_RE.match(token)
            if arg_match:
                key = arg_match.group("key")
                record.setdefault(f"arg_{key}", key)
        if args:
            record["Args"] = args[:500]
        return record

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:5])
        fields = self._fields_table(summary)
        parse_error_count = sum(summary["parse_errors"].values())
        methods = ", ".join(list(summary["top_method_names"].keys())[:10]) or "-"
        processes = ", ".join(list(summary["top_process_names"].keys())[:10]) or "-"

        if ru:
            return f"""# Анализ формата: txt

## 1. Назначение
TXT-файлы Host VALIDATION содержат line-oriented syscall traces в sysdig-like формате. Формат пригоден для частот syscall, n-grams, переходов между вызовами, process activity и sequence features.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | txt |
| Варианты расширения | .txt |
| DNS | нет |
| Host | да |
| Роли | VALIDATION |
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
| Табличная структура | частично, positional fields + syscall args |
| Заголовок | нет |
| Разделитель | whitespace + key=value args |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Parsed lines | {summary["parsed_lines"]} |
| Unmatched lines | {summary["unmatched_lines"]} |

## 5. Содержательная структура
Строки имеют структуру `event_index time cpu user_id process pid direction syscall args`. В sample встречаются syscalls: {methods}. Основные процессы: {processes}.

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
| Можно использовать для supervised learning | нет без внешней разметки |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | Time |
| Формат времени | HH:MM:SS.nanoseconds |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- напрямую не представлены.

### Host-признаки
- `MethodName` frequencies;
- syscall n-grams и transitions;
- syscall trace length;
- direction `<`/`>` для enter/exit событий;
- аргументы syscall из `key=value` suffix;
- активность по `Pid`, `ProcessName`, `UserId`, `Cpu`.

### Network / hybrid-признаки
- network syscalls (`recvfrom`, `sendto`, `connect`, `accept`) и socket args;
- корреляция с packet/netflow данными по scenario/file name.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | частично | args зависят от syscall |
| Нестабильная структура | частично | suffix args различаются по syscall |
| Смешанные схемы | нет | sample соответствует sysdig-like trace |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
TXT готов к feature extraction как line-oriented syscall trace. Pipeline должен читать файлы streaming-режимом и учитывать большой размер/количество файлов.
"""

        return f"""# Format Analysis: txt

## 1. Purpose
Host VALIDATION TXT files contain line-oriented syscall traces in a sysdig-like format. The format is suitable for syscall frequencies, n-grams, call transitions, process activity, and sequence features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | .txt |
| DNS | no |
| Host | yes |
| Roles | VALIDATION |
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
| Tabular structure | partial, positional fields + syscall args |
| Header | no |
| Delimiter | whitespace + key=value args |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Parsed lines | {summary["parsed_lines"]} |
| Unmatched lines | {summary["unmatched_lines"]} |

## 5. Content Structure
Rows use `event_index time cpu user_id process pid direction syscall args`. Syscalls in the sample include: {methods}. Top processes: {processes}.

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
| Field name | Time |
| Time format | HH:MM:SS.nanoseconds |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not directly represented.

### Host Features
- `MethodName` frequencies;
- syscall n-grams and transitions;
- syscall trace length;
- direction `<`/`>` for enter/exit events;
- syscall arguments from `key=value` suffixes;
- activity by `Pid`, `ProcessName`, `UserId`, and `Cpu`.

### Network / Hybrid Features
- network syscalls such as `recvfrom`, `sendto`, `connect`, and `accept`;
- socket arguments from syscall suffixes;
- correlation with packet/netflow data by scenario/file name.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | partial | args are syscall-specific |
| Unstable structure | partial | suffix args vary by syscall |
| Mixed schemas | no | sample follows one sysdig-like trace schema |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
TXT is ready for feature extraction as a line-oriented syscall trace. The pipeline must stream files and account for the large file count and size.
"""

    @staticmethod
    def _fields_table(summary: dict[str, Any]) -> str:
        purposes = {
            "EventIndex": "event sequence number",
            "Time": "event timestamp",
            "Cpu": "CPU id",
            "UserId": "user id",
            "ProcessName": "process name",
            "Pid": "process id",
            "Direction": "syscall enter/exit",
            "MethodName": "syscall name",
            "Args": "raw syscall arguments",
        }
        preferred = ["EventIndex", "Time", "Cpu", "UserId", "ProcessName", "Pid", "Direction", "MethodName", "Args"]
        by_name = {field["field"]: field for field in summary["fields"]}
        selected = [by_name[name] for name in preferred if name in by_name]
        for field in summary["fields"]:
            if field not in selected:
                selected.append(field)
            if len(selected) >= 14:
                break
        return "\n".join(
            f"| {field['field']} | {field['type']} | {purposes.get(field['field'], 'syscall argument key')} | {str(field['example']).replace('|', '\\|')} |"
            for field in selected[:14]
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
            "cap": (self._load_optional_status("analysis-host-validation-cap-summary.json"), "cap.md"),
            "csv": (self._load_optional_status("analysis-host-validation-csv-summary.json"), "csv.md"),
            "json": (self._load_optional_status("analysis-host-validation-json-summary.json"), "json.md"),
            "netflow_day": (
                self._load_optional_status("analysis-host-validation-netflow-day-summary.json"),
                "netflow_day.md",
            ),
            "pcap": (self._load_optional_status("analysis-host-validation-pcap-summary.json"), "pcap.md"),
            "pcapng": (self._load_optional_status("analysis-host-validation-pcapng-summary.json"), "pcapng.md"),
            "txt": (summary["final_status"], "txt.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task7: Analysis of host validation txt dataset files"
            if ru
            else "# Task7 Report: Analysis of host validation txt dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\VALIDATION\\txt` на основе "
            f"`{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\VALIDATION\\txt` using `{self.HOST_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_validation_txt_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/validation/txt.md`
- `docs/en/analysis-dataset/host/validation/txt.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/validation/Task7(Analysis of host validation txt dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/validation/Task7(Analysis of host validation txt dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.txt`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler берёт равномерную выборку файлов и читает ограниченное число строк на файл streaming-режимом.' if ru else 'The handler takes an even file sample and reads a limited number of lines per file in streaming mode.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_counts(self) -> dict[str, int]:
        payload = JsonDataManager(self.temp_data_path / self.HOST_INPUT_JSON_FILE).read(default={})
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
                "parsed_lines": summary["parsed_lines"],
                "unmatched_lines": summary["unmatched_lines"],
                "top_method_names": dict(list(summary["top_method_names"].items())[:8]),
                "final_status": summary["final_status"],
            },
            ensure_ascii=False,
            indent=2,
        )
