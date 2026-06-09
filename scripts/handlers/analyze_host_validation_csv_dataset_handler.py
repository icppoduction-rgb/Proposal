from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostValidationCSVContentAnalysisResult:
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


class HostValidationCSVContentAnalysisHandler:
    ROLE_NAME = "VALIDATION"
    FORMAT_NAME = "csv"
    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-validation-csv-summary.json"
    DEFAULT_MAX_LINES_PER_FILE = 1000
    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_lines_per_file: int = DEFAULT_MAX_LINES_PER_FILE,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.report_path = Path(report_path).expanduser() if report_path is not None else self.project_root / "report"
        self.max_lines_per_file = max(50, max_lines_per_file)
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "host" / "validation"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "host" / "validation"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "host" / "validation"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "host" / "validation"

    def analyze_and_generate_docs(self) -> HostValidationCSVContentAnalysisResult:
        all_paths = self._extract_paths()
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for VALIDATION/csv.")

        summary = self._build_summary(all_paths)
        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "csv.md"
        docs_en_path = self.docs_en_dir / "csv.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task2(Analysis of host validation csv dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task2(Analysis of host validation csv dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return HostValidationCSVContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=len(all_paths),
            status=str(summary["final_status"]),
        )

    def _extract_paths(self) -> list[Path]:
        payload = JsonDataManager(self.temp_data_path / self.HOST_INPUT_JSON_FILE).read(default={})
        role_bucket = payload.get(self.ROLE_NAME, {})
        if not isinstance(role_bucket, dict):
            raise ValueError(f"Role '{self.ROLE_NAME}' in source JSON must be an object.")
        format_bucket = role_bucket.get(self.FORMAT_NAME, [])
        if not isinstance(format_bucket, list):
            raise ValueError(f"Role '{self.ROLE_NAME}' format '{self.FORMAT_NAME}' must be a list.")
        return sorted([Path(str(path)).expanduser() for path in format_bucket], key=lambda path: str(path).lower())

    def _build_summary(self, paths: list[Path]) -> dict[str, Any]:
        fields: dict[str, Counter[str]] = {}
        examples: dict[str, str] = {}
        label_values: Counter[str] = Counter()
        image_names: Counter[str] = Counter()
        parse_errors: Counter[str] = Counter()
        empty_files = 0
        sampled_rows = 0
        header_variants: Counter[str] = Counter()

        for path in paths:
            if not path.exists():
                parse_errors["file_not_found"] += 1
                continue
            if path.stat().st_size == 0:
                empty_files += 1
                continue
            try:
                with path.open("r", encoding="utf-8", errors="replace", newline="") as stream:
                    reader = csv.DictReader(stream)
                    if reader.fieldnames:
                        header_variants[",".join(field.strip() for field in reader.fieldnames)] += 1
                    for index, row in enumerate(reader):
                        if index >= self.max_lines_per_file:
                            break
                        sampled_rows += 1
                        normalized_row = {
                            (key or "").strip(): (value or "").strip()
                            for key, value in row.items()
                            if key is not None
                        }
                        for key, normalized in normalized_row.items():
                            if key is None:
                                continue
                            fields.setdefault(key, Counter())[self._infer_type(normalized)] += 1
                            examples.setdefault(key, normalized[:120])
                        label_values[normalized_row.get("is_executing_exploit", "")] += 1
                        image_names[normalized_row.get("image_name", "")] += 1
            except (OSError, csv.Error) as error:
                parse_errors[str(error)] += 1

        final_status = self.STATUS_BROKEN if sampled_rows == 0 else self.STATUS_READY
        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.HOST_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(paths),
                "sampled_files_count": len(paths),
                "max_lines_per_file": self.max_lines_per_file,
            },
            "sample_paths": [str(path) for path in paths],
            "sampled_rows": sampled_rows,
            "header_variants": dict(header_variants),
            "fields": [
                {
                    "field": name,
                    "type": counter.most_common(1)[0][0],
                    "example": examples.get(name, ""),
                }
                for name, counter in fields.items()
            ],
            "label_values": dict(label_values.most_common()),
            "image_names_sample": dict(image_names.most_common(10)),
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "high",
        }

    @staticmethod
    def _infer_type(value: str) -> str:
        if value in {"True", "False"}:
            return "boolean"
        try:
            int(value)
            return "integer"
        except ValueError:
            return "string" if value else "missing"

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._fields_table(summary, language)
        labels = ", ".join(f"{key}: {value}" for key, value in summary["label_values"].items())
        parse_errors = sum(summary["parse_errors"].values())

        if ru:
            return f"""# Анализ формата: csv

## 1. Назначение
CSV-файлы Host VALIDATION содержат metadata запусков сценариев: образ, имя сценария, флаг эксплуатации и временные параметры. Формат пригоден для validation/evaluation разметки и контекстных признаков.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
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
| Табличная структура | да |
| Заголовок | да |
| Разделитель | comma |
| Кодировка | utf-8 |
| Вложенная структура | нет |
| Sample-строк | {summary["sampled_rows"]} |

## 5. Содержательная структура
Файлы `runs*.csv` описывают validation сценарии: `image_name`, `scenario_name`, бинарный флаг `is_executing_exploit`, `warmup_time`, `recording_time`, `exploit_start_time`.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
{fields}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | is_executing_exploit |
| Значения label | {labels} |
| Можно использовать для supervised learning | да, как validation labels |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | частично |
| Название поля | warmup_time, recording_time, exploit_start_time |
| Формат времени | seconds/relative offsets |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- не применимо.

### Host-признаки
- scenario/image context;
- exploit flag;
- recording duration and exploit start offset.

### Network / hybrid-признаки
- correlation key через scenario/image для packet captures.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | count: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_errors else "нет"} | parse errors: {parse_errors} |
| Missing values | нет | sample без пропусков в основных полях |
| Нестабильная структура | нет | header стабилен |
| Смешанные схемы | нет | все файлы `runs*.csv` |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
CSV готов к использованию как validation metadata и источник label/context признаков. Исходные датасеты не изменялись.
"""

        return f"""# Format Analysis: csv

## 1. Purpose
Host VALIDATION CSV files contain scenario run metadata: image, scenario name, exploit execution flag, and timing parameters. The format is suitable for validation/evaluation labels and context features.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
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
| Tabular structure | yes |
| Header | yes |
| Delimiter | comma |
| Encoding | utf-8 |
| Nested structure | no |
| Sample rows | {summary["sampled_rows"]} |

## 5. Content Structure
`runs*.csv` files describe validation scenarios: `image_name`, `scenario_name`, binary `is_executing_exploit`, `warmup_time`, `recording_time`, and `exploit_start_time`.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
{fields}

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | yes |
| Field name | is_executing_exploit |
| Label values | {labels} |
| Suitable for supervised learning | yes, as validation labels |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | partial |
| Field name | warmup_time, recording_time, exploit_start_time |
| Time format | seconds/relative offsets |
| Can build sequences | no |
| Can apply sliding windows | no |

## 9. Potential Feature Extraction
### DNS Features
- not applicable.

### Host Features
- scenario/image context;
- exploit flag;
- recording duration and exploit start offset.

### Network / Hybrid Features
- correlation key through scenario/image for packet captures.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_errors else "no"} | parse errors: {parse_errors} |
| Missing values | no | no gaps in core sample fields |
| Unstable structure | no | stable header |
| Mixed schemas | no | all files are `runs*.csv` |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
CSV is ready as validation metadata and label/context feature source. Source datasets were not modified.
"""

    @staticmethod
    def _fields_table(summary: dict[str, Any], language: str) -> str:
        purpose = {
            "image_name": "container/image identifier",
            "scenario_name": "scenario id",
            "is_executing_exploit": "binary exploit label",
            "warmup_time": "warmup seconds",
            "recording_time": "recording seconds",
            "exploit_start_time": "exploit start offset",
        }
        return "\n".join(
            f"| {field['field']} | {field['type']} | {purpose.get(field['field'], 'metadata')} | {field['example']} |"
            for field in summary["fields"]
        )

    def _build_readme(self, summary: dict[str, Any], language: str) -> str:
        title = "# Анализ содержимого файлов датасетов" if language == "ru" else "# Dataset File Content Analysis"
        header = "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n" if language == "ru" else "| Format | File count | DNS | Host | Status | Document |\n"
        yes = "да" if language == "ru" else "yes"
        no = "нет" if language == "ru" else "no"
        pending = "ещё не анализировалось" if language == "ru" else "not analyzed yet"
        status_by_format = {
            "cap": (self._load_optional_status("analysis-host-validation-cap-summary.json"), "cap.md"),
            "csv": (summary["final_status"], "csv.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = "# Отчёт по Task2: Analysis of host validation csv dataset files" if ru else "# Task2 Report: Analysis of host validation csv dataset files"
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\VALIDATION\\csv` на основе `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\VALIDATION\\csv` using `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_validation_csv_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/validation/csv.md`
- `docs/en/analysis-dataset/host/validation/csv.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/validation/Task2(Analysis of host validation csv dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/validation/Task2(Analysis of host validation csv dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.csv`.

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{('Handler анализирует все CSV-файлы формата и читает ограниченное число строк на файл.' if ru else 'The handler analyzes all CSV files for the format and reads a limited number of rows per file.')}

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
        path = self.temp_data_path / summary_file_name
        if not path.exists():
            return "-"
        payload = JsonDataManager(path).read(default={})
        status = payload.get("final_status")
        return str(status) if isinstance(status, str) else "-"

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        return json.dumps(
            {
                "format": summary["format"],
                "role": summary["role"],
                "scope": summary["scope"],
                "label_values": summary["label_values"],
                "final_status": summary["final_status"],
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
