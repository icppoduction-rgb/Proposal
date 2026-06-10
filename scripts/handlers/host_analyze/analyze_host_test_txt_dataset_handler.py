from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class HostTestTXTContentAnalysisResult:
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
class TXTProbe:
    path: str
    file_name: str
    file_size_bytes: int
    sampled_lines: int
    parsed_lines: int
    unmatched_lines: int
    parse_error: str | None


class HostTestTXTContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "txt"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-test-txt-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    REQUIRED_FIELDS = {"Time", "Pid", "MethodName", "ProcessName"}

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
        self.max_lines_per_file = max(50, max_lines_per_file)

        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host" / "test"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host" / "test"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "host" / "test"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "host" / "test"

    def analyze_and_generate_docs(self) -> HostTestTXTContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TEST/txt.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "txt.md"
        docs_en_path = self.docs_en_dir / "txt.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task49(Analysis of host test txt dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task49(Analysis of host test txt dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary_payload, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary_payload, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary_payload, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary_payload, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary_payload, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary_payload, summary_json_path, "en"))

        return HostTestTXTContentAnalysisResult(
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
        selected = [path for path in all_paths if path.name.lower() == "name.txt"]
        step = (len(all_paths) - 1) / (self.max_files_per_format - 1)
        for index in sorted({int(round(i * step)) for i in range(self.max_files_per_format)}):
            candidate = all_paths[index]
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) >= self.max_files_per_format:
                break
        return selected

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        probes: list[TXTProbe] = []
        field_types: dict[str, Counter[str]] = {}
        examples: dict[str, str] = {}
        method_names: Counter[str] = Counter()
        process_names: Counter[str] = Counter()
        file_prefixes: Counter[str] = Counter()
        parse_errors: Counter[str] = Counter()
        empty_files = 0

        for path in sampled_paths:
            probe, records = self._probe_file(path)
            probes.append(probe)
            if probe.file_size_bytes == 0:
                empty_files += 1
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            file_prefixes[path.name.split("__", 1)[0]] += 1

            for record in records:
                for key, value in record.items():
                    field_types.setdefault(key, Counter())[self._infer_type(value)] += 1
                    examples.setdefault(key, value[:120])
                if "MethodName" in record:
                    method_names[record["MethodName"]] += 1
                if "ProcessName" in record:
                    process_names[Path(record["ProcessName"]).name or record["ProcessName"]] += 1

        parsed_lines = sum(probe.parsed_lines for probe in probes)
        unmatched_lines = sum(probe.unmatched_lines for probe in probes)
        if parsed_lines == 0:
            final_status = self.STATUS_BROKEN
        elif unmatched_lines > parsed_lines:
            final_status = self.STATUS_PARTIAL
        else:
            final_status = self.STATUS_READY

        fields = []
        for field_name, counter in sorted(field_types.items()):
            fields.append(
                {
                    "field": field_name,
                    "type": counter.most_common(1)[0][0],
                    "example": examples.get(field_name, ""),
                }
            )

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
            "fields": fields,
            "parsed_lines": parsed_lines,
            "unmatched_lines": unmatched_lines,
            "top_method_names": dict(method_names.most_common(20)),
            "top_process_names": dict(process_names.most_common(20)),
            "sampled_file_prefixes": dict(file_prefixes.most_common(20)),
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "high",
        }

    def _probe_file(self, path: Path) -> tuple[TXTProbe, list[dict[str, str]]]:
        if not path.exists():
            return TXTProbe(str(path), path.name, 0, 0, 0, 0, "file_not_found"), []
        file_size = path.stat().st_size
        if file_size == 0:
            return TXTProbe(str(path), path.name, 0, 0, 0, 0, "empty_file"), []

        records: list[dict[str, str]] = []
        unmatched = 0
        try:
            with path.open("r", encoding="utf-8", errors="replace") as stream:
                for index, raw_line in enumerate(stream):
                    if index >= self.max_lines_per_file:
                        break
                    line = raw_line.strip()
                    if not line:
                        continue
                    record = self._parse_key_value_line(line)
                    if record is None:
                        unmatched += 1
                        continue
                    records.append(record)
        except OSError as error:
            return TXTProbe(str(path), path.name, file_size, 0, 0, 0, str(error)), []

        return (
            TXTProbe(
                path=str(path),
                file_name=path.name,
                file_size_bytes=file_size,
                sampled_lines=len(records) + unmatched,
                parsed_lines=len(records),
                unmatched_lines=unmatched,
                parse_error=None,
            ),
            records,
        )

    def _parse_key_value_line(self, line: str) -> dict[str, str] | None:
        parts = line.split(",")
        record: dict[str, str] = {}
        for part in parts:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            if key:
                record[key] = value.strip()
        if self.REQUIRED_FIELDS.issubset(record):
            return record
        return None

    @staticmethod
    def _infer_type(value: str) -> str:
        if value == "":
            return "missing"
        try:
            int(value)
            return "integer"
        except ValueError:
            return "string"

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._render_fields(summary, language)
        methods = ", ".join(list(summary["top_method_names"].keys())[:8])
        parse_error_count = sum(summary["parse_errors"].values())

        if ru:
            return f"""# Анализ формата: txt

## 1. Назначение
TXT-файлы Host TEST содержат line-oriented трассы Windows NT syscall/API событий в формате `key=value`. Формат нужен для извлечения syscall frequencies, n-grams, process activity и sequence-признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | txt |
| Варианты расширения | .txt |
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
| Табличная структура | частично, key=value |
| Заголовок | нет |
| Разделитель | comma + key=value |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Parsed lines | {summary["parsed_lines"]} |

## 5. Содержательная структура
Основная схема: `Time`, `Pid`, `MethodName`, `ProcessName` и дополнительные `argN`. Имена файлов также кодируют syscall method (`ZwAccessCheck__...txt`). В sample встречаются методы: {methods}. `name.txt` является служебным файлом с sample executable path/pid и не имеет основной схемы.

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
| Можно использовать для supervised learning | нет без внешних меток |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | Time |
| Формат времени | числовой relative timestamp |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- частоты `MethodName`;
- n-grams syscall/API;
- переходы между вызовами;
- длина syscall trace;
- параметры `argN`;
- активность по `Pid` и `ProcessName`;
- command/path tokens из `ProcessName`.

### Network / hybrid-признаки
- прямые flow/network поля не обнаружены;
- возможна корреляция с network по внешнему sample id.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | частично | `argN` присутствуют не во всех методах |
| Нестабильная структура | частично | набор `argN` зависит от метода |
| Смешанные схемы | частично | `name.txt` служебный, основная масса syscall traces |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
TXT готов к feature extraction для syscall/API sequence-признаков. Нужно учитывать очень большое число файлов, метод-специфичные `argN` и служебный `name.txt`.
"""

        return f"""# Format Analysis: txt

## 1. Purpose
Host TEST TXT files contain line-oriented Windows NT syscall/API traces in `key=value` format. The format is useful for syscall frequencies, n-grams, process activity, and sequence features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | .txt |
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
| Tabular structure | partial, key=value |
| Header | no |
| Delimiter | comma + key=value |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Parsed lines | {summary["parsed_lines"]} |

## 5. Content Structure
The main schema is `Time`, `Pid`, `MethodName`, `ProcessName`, plus method-specific `argN` values. File names also encode the syscall method (`ZwAccessCheck__...txt`). Methods in sample include: {methods}. `name.txt` is a service file with executable path/pid metadata and does not follow the main schema.

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
| Time format | numeric relative timestamp |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- not applicable.

### Host Features
- `MethodName` frequencies;
- syscall/API n-grams;
- call transitions;
- syscall trace length;
- `argN` parameters;
- activity by `Pid` and `ProcessName`;
- command/path tokens from `ProcessName`.

### Network / Hybrid Features
- direct flow/network fields were not detected;
- correlation with network data may be possible through an external sample id.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | partial | `argN` fields are method-specific |
| Unstable structure | partial | `argN` set depends on method |
| Mixed schemas | partial | `name.txt` is service metadata, most files are syscall traces |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
TXT is ready for syscall/API sequence feature extraction. The pipeline must account for the very large file count, method-specific `argN` fields, and service `name.txt`.
"""

    @staticmethod
    def _render_fields(summary: dict[str, Any], language: str) -> str:
        purposes = {
            "Time": "relative timestamp" if language == "en" else "relative timestamp",
            "Pid": "process id" if language == "en" else "process id",
            "MethodName": "syscall/API method" if language == "en" else "syscall/API method",
            "ProcessName": "process path" if language == "en" else "путь процесса",
        }
        preferred = ["Time", "Pid", "MethodName", "ProcessName", "arg1", "arg2", "arg3", "arg4"]
        by_name = {field["field"]: field for field in summary["fields"]}
        selected = [by_name[name] for name in preferred if name in by_name]
        for field in summary["fields"]:
            if field not in selected:
                selected.append(field)
            if len(selected) >= 14:
                break
        rows = []
        for field in selected:
            purpose = purposes.get(
                field["field"],
                "method-specific argument" if language == "en" else "method-specific argument",
            )
            example = str(field["example"]).replace("|", "\\|")
            rows.append(f"| {field['field']} | {field['type']} | {purpose} | {example} |")
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
            "bson": (self._load_optional_status("analysis-host-test-bson-summary.json"), "bson.md"),
            "csv": (self._load_optional_status("analysis-host-test-csv-summary.json"), "csv.md"),
            "json": (self._load_optional_status("analysis-host-test-json-summary.json"), "json.md"),
            "log": (self._load_optional_status("analysis-host-test-log-summary.json"), "log.md"),
            "netflow_day": (self._load_optional_status("analysis-host-test-netflow-day-summary.json"), "netflow_day.md"),
            "txt": (summary["final_status"], "txt.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_host_test_format_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host TEST)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task49: Analysis of host test txt dataset files"
            if ru
            else "# Task49 Report: Analysis of host test txt dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\TEST\\txt` на основе `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\TEST\\txt` using `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_test_txt_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/txt.md`
- `docs/en/analysis-dataset/host/test/txt.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/test/Task49(Analysis of host test txt dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/test/Task49(Analysis of host test txt dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `TEST.txt`.

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{('Handler берёт равномерную выборку по огромному списку TXT-файлов и читает ограниченное число строк на файл.' if ru else 'The handler takes an even sample from the large TXT file list and reads a limited number of lines per file.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

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
            "top_method_names": dict(list(summary["top_method_names"].items())[:5]),
            "final_status": summary["final_status"],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
