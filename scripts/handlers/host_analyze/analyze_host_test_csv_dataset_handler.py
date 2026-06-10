from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class HostTestCSVContentAnalysisResult:
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
class CSVProbe:
    path: str
    file_name: str
    file_size_bytes: int
    encoding: str
    delimiter: str
    has_header: bool
    sampled_rows: int
    column_count: int
    missing_cells: int
    duplicate_rows: int
    parse_error: str | None


class HostTestCSVContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "csv"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 1000

    HOST_INPUT_JSON_FILE = "sort-path-host-file.json"
    SUMMARY_JSON_FILE = "analysis-host-test-csv-summary.json"

    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1252", "latin-1")

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

    def analyze_and_generate_docs(self) -> HostTestCSVContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for TEST/csv.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary_payload)

        docs_ru_path = self.docs_ru_dir / "csv.md"
        docs_en_path = self.docs_en_dir / "csv.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task45(Analysis of host test csv dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task45(Analysis of host test csv dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_ru_readme(summary_payload))
        self._write_text_file(docs_en_readme_path, self._build_en_readme(summary_payload))
        self._write_text_file(report_ru_path, self._build_ru_report(summary_payload, summary_json_path))
        self._write_text_file(report_en_path, self._build_en_report(summary_payload, summary_json_path))

        return HostTestCSVContentAnalysisResult(
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
        return all_paths[: self.max_files_per_format]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        probes: list[CSVProbe] = []
        header_counter: Counter[str] = Counter()
        type_by_column: dict[str, Counter[str]] = {}
        examples_by_column: dict[str, str] = {}
        label_values: Counter[str] = Counter()
        empty_files = 0
        parse_errors: Counter[str] = Counter()

        for path in sampled_paths:
            probe, rows, header = self._probe_file(path)
            probes.append(probe)
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1
            if probe.file_size_bytes == 0:
                empty_files += 1

            for column in header:
                header_counter[column] += 1
                type_by_column.setdefault(column, Counter())

            for row in rows:
                for column, value in zip(header, row):
                    normalized = value.strip()
                    type_by_column.setdefault(column, Counter())[self._infer_type(normalized)] += 1
                    if normalized and column not in examples_by_column:
                        examples_by_column[column] = normalized[:120]
                    if column.lower() == "label" and normalized:
                        label_values[normalized] += 1

        parsed_files = sum(1 for probe in probes if probe.parse_error is None)
        final_status = self.STATUS_BROKEN if parsed_files == 0 else self.STATUS_PARTIAL
        fields = []
        for column, count in header_counter.most_common(50):
            type_counts = type_by_column.get(column, Counter())
            dominant_type = type_counts.most_common(1)[0][0] if type_counts else "unknown"
            fields.append(
                {
                    "field": column,
                    "type": dominant_type,
                    "observed_files": count,
                    "example": examples_by_column.get(column, ""),
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
            "sample_paths": [str(path) for path in sampled_paths],
            "file_probes": [probe.__dict__ for probe in probes],
            "fields": fields,
            "label_values": dict(label_values.most_common(30)),
            "empty_files_in_sample": empty_files,
            "parse_errors": dict(parse_errors),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "high",
        }

    def _probe_file(self, path: Path) -> tuple[CSVProbe, list[list[str]], list[str]]:
        if not path.exists():
            return (
                CSVProbe(str(path), path.name, 0, "missing", ",", False, 0, 0, 0, 0, "file_not_found"),
                [],
                [],
            )
        file_size = path.stat().st_size
        if file_size == 0:
            return (
                CSVProbe(str(path), path.name, 0, "empty", ",", False, 0, 0, 0, 0, "empty_file"),
                [],
                [],
            )

        encoding = self._detect_encoding(path)
        try:
            with path.open("r", encoding=encoding, errors="replace", newline="") as stream:
                sample_text = stream.read(8192)
                stream.seek(0)
                dialect = csv.Sniffer().sniff(sample_text, delimiters=",;\t|")
                reader = csv.reader(stream, dialect)
                rows: list[list[str]] = []
                for index, row in enumerate(reader):
                    if index >= self.max_lines_per_file:
                        break
                    rows.append(row)
        except (OSError, csv.Error) as error:
            return (
                CSVProbe(str(path), path.name, file_size, encoding, ",", False, 0, 0, 0, 0, str(error)),
                [],
                [],
            )

        if not rows:
            return (
                CSVProbe(str(path), path.name, file_size, encoding, ",", False, 0, 0, 0, 0, "no_rows"),
                [],
                [],
            )

        header = rows[0]
        data_rows = rows[1:]
        delimiter = getattr(dialect, "delimiter", ",")
        expected_columns = len(header)
        missing_cells = sum(1 for row in data_rows for value in row if value == "")
        duplicate_rows = len(data_rows) - len({tuple(row) for row in data_rows})

        return (
            CSVProbe(
                path=str(path),
                file_name=path.name,
                file_size_bytes=file_size,
                encoding=encoding,
                delimiter=delimiter,
                has_header=True,
                sampled_rows=len(data_rows),
                column_count=expected_columns,
                missing_cells=missing_cells,
                duplicate_rows=duplicate_rows,
                parse_error=None,
            ),
            data_rows,
            header,
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
    def _infer_type(value: str) -> str:
        if value == "":
            return "missing"
        try:
            int(value, 0)
            return "integer"
        except ValueError:
            pass
        try:
            float(value)
            return "float"
        except ValueError:
            pass
        if value.count(".") == 3 and all(part.isdigit() for part in value.split(".")):
            return "ip"
        return "string"

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._render_fields(summary, language="ru")
        labels = ", ".join(summary["label_values"].keys()) or "не обнаружены"
        parse_error_count = sum(summary["parse_errors"].values())
        return f"""# Анализ формата: csv

## 1. Назначение
CSV-файлы Host TEST содержат packet/network metadata и отдельные CSV-карты меток атак. Формат нужен для анализа сетевого поведения и возможной host+network корреляции, но TEST-набор не должен использоваться для обучения.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | csv |
| Варианты расширения | .csv |
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
| Табличная структура | да |
| Заголовок | да |
| Разделитель | comma |
| Кодировка | utf-8/utf-8-sig по sample |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |

## 5. Содержательная структура
`attack_dataset.csv` содержит packet metadata: frame time, epoch time, IP/TCP поля, адреса, порты, flags, длины и checksum. `attack_labels.csv` и `attack_labels_sbseg.csv` содержат соответствие `ip -> label` для атак вроде nmap scan. Это network/hybrid-структура внутри Host TEST bucket.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
{fields}

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | да |
| Название поля | label в отдельных label CSV; `attack_dataset.csv` label не содержит |
| Значения label | {labels} |
| Можно использовать для supervised learning | частично; нужен join по IP и TEST нельзя применять для обучения |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | да |
| Название поля | frame_info.time, frame_info.time_epoch |
| Формат времени | строка Wireshark timestamp + epoch seconds |
| Можно строить sequence | да |
| Можно применять sliding window | да |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- прямые DNS-поля в sample не обнаружены.

### Host-признаки
- прямые syscall/process признаки не обнаружены.

### Network / hybrid-признаки
- bytes/packet length по `frame_info.len`, `ip.len`, `tcp.len`;
- протоколы и TCP flags;
- пары `ip.src`/`ip.dst` и source/destination ports;
- временные интервалы между пакетами по `frame_info.time_epoch`;
- attack label через join по IP;
- host + network correlation features при наличии внешней связи с host traces.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["empty_files_in_sample"] else "нет"} | в sample: {summary["empty_files_in_sample"]} |
| Повреждённые файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | да | в packet CSV есть пустые protocol/header поля |
| Нестабильная структура | да | dataset CSV и label CSV имеют разные схемы |
| Смешанные схемы | да | 41-колоночный packet CSV и 2-колоночные label maps |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | высокий |

## 12. Вывод
CSV в Host TEST пригоден для network/hybrid feature extraction, но не является единым host telemetry CSV. Для supervised evaluation метки нужно присоединять отдельно по IP; TEST-данные не использовать для обучения.
"""

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        examples = "\n".join(summary["sample_paths"][:3])
        fields = self._render_fields(summary, language="en")
        labels = ", ".join(summary["label_values"].keys()) or "not detected"
        parse_error_count = sum(summary["parse_errors"].values())
        return f"""# Format Analysis: csv

## 1. Purpose
Host TEST CSV files contain packet/network metadata and separate CSV attack-label maps. The format is useful for network behaviour analysis and possible host+network correlation; TEST data must not be used for training.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | csv |
| Extension variants | .csv |
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
| Tabular structure | yes |
| Header | yes |
| Delimiter | comma |
| Encoding | utf-8/utf-8-sig in sample |
| Nested structure | no |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |

## 5. Content Structure
`attack_dataset.csv` contains packet metadata: frame time, epoch time, IP/TCP fields, addresses, ports, flags, lengths, and checksums. `attack_labels.csv` and `attack_labels_sbseg.csv` contain `ip -> label` mappings for attacks such as nmap scans. This is a network/hybrid structure inside the Host TEST bucket.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
{fields}

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | yes |
| Field name | label in separate label CSV files; `attack_dataset.csv` has no label column |
| Label values | {labels} |
| Suitable for supervised learning | partial; requires IP join, and TEST must not be used for training |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | yes |
| Field name | frame_info.time, frame_info.time_epoch |
| Time format | Wireshark timestamp string + epoch seconds |
| Can build sequences | yes |
| Can apply sliding windows | yes |

## 9. Potential Feature Extraction
### DNS Features
- direct DNS fields were not detected in the sample.

### Host Features
- direct syscall/process features were not detected.

### Network / Hybrid Features
- bytes/packet length from `frame_info.len`, `ip.len`, `tcp.len`;
- protocols and TCP flags;
- `ip.src`/`ip.dst` pairs and source/destination ports;
- packet inter-arrival times from `frame_info.time_epoch`;
- attack labels through an IP join;
- host + network correlation features if external metadata links these files to host traces.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["empty_files_in_sample"] else "no"} | sample count: {summary["empty_files_in_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | yes | packet CSV contains empty protocol/header fields |
| Unstable structure | yes | dataset CSV and label CSV files use different schemas |
| Mixed schemas | yes | one 41-column packet CSV and two 2-column label maps |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | high |

## 12. Conclusion
Host TEST CSV is suitable for network/hybrid feature extraction, but it is not a single host telemetry CSV. Labels must be joined separately by IP for supervised evaluation; TEST data must not be used for training.
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
            "csv": (summary["final_status"], "csv.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_host_test_format_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host TEST)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_ru_report(self, summary: dict[str, Any], summary_json_path: Path) -> str:
        return f"""# Отчёт по Task45: Analysis of host test csv dataset files

## Описание задачи
Выполнен анализ содержимого файлов `PATH_HOST_DATASETS_FILTER\\TEST\\csv` на основе путей из `{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_test_csv_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/csv.md`
- `docs/en/analysis-dataset/host/test/csv.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/test/Task45(Analysis of host test csv dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/test/Task45(Analysis of host test csv dataset files)_report.md`

## Структура JSON
Источник `{self.HOST_INPUT_JSON_FILE}` имеет структуру `role -> format -> list[path]`. Для задачи использован bucket `TEST.csv`.

## Логика группировки путей
Handler читает Host JSON, выбирает роль `TEST` и формат `csv`, сортирует пути и анализирует до {self.max_files_per_format} файлов. Для каждого CSV читается до {self.max_lines_per_file} строк.

## Пример итогового JSON
```json
{self._summary_json_excerpt(summary)}
```

## Результат
Создан summary `{summary_json_path}`. Итоговый статус: `{summary["final_status"]}`.
"""

    def _build_en_report(self, summary: dict[str, Any], summary_json_path: Path) -> str:
        return f"""# Task45 Report: Analysis of host test csv dataset files

## Task Description
Analyzed files under `PATH_HOST_DATASETS_FILTER\\TEST\\csv` using paths from `{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_test_csv_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/test/csv.md`
- `docs/en/analysis-dataset/host/test/csv.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/test/Task45(Analysis of host test csv dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/test/Task45(Analysis of host test csv dataset files)_report.md`

## JSON Structure
The source `{self.HOST_INPUT_JSON_FILE}` is structured as `role -> format -> list[path]`. This task uses the `TEST.csv` bucket.

## Path Grouping Logic
The handler reads the Host JSON, selects role `TEST` and format `csv`, sorts paths, and analyzes up to {self.max_files_per_format} files. For each CSV, up to {self.max_lines_per_file} rows are read.

## Result JSON Example
```json
{self._summary_json_excerpt(summary)}
```

## Result
Created summary `{summary_json_path}`. Final status: `{summary["final_status"]}`.
"""

    @staticmethod
    def _render_fields(summary: dict[str, Any], language: str) -> str:
        purposes = {
            "frame_info.time": "packet timestamp" if language == "en" else "время пакета",
            "frame_info.time_epoch": "epoch seconds" if language == "en" else "epoch seconds",
            "ip.src": "source IP" if language == "en" else "source IP",
            "ip.dst": "destination IP" if language == "en" else "destination IP",
            "tcp.srcport": "source TCP port" if language == "en" else "source TCP port",
            "tcp.dstport": "destination TCP port" if language == "en" else "destination TCP port",
            "tcp.flags": "TCP flags" if language == "en" else "TCP flags",
            "label": "attack class label" if language == "en" else "метка класса атаки",
        }
        preferred = [
            "frame_info.time",
            "frame_info.time_epoch",
            "ip.src",
            "ip.dst",
            "ip.proto",
            "tcp.srcport",
            "tcp.dstport",
            "tcp.flags",
            "frame_info.len",
            "ip.len",
            "label",
        ]
        by_name = {field["field"]: field for field in summary["fields"]}
        selected = [by_name[name] for name in preferred if name in by_name]
        for field in summary["fields"]:
            if field not in selected:
                selected.append(field)
            if len(selected) >= 18:
                break
        rows = []
        for field in selected[:18]:
            name = str(field["field"])
            purpose = purposes.get(name, "sampled CSV column" if language == "en" else "колонка sample CSV")
            example = str(field["example"]).replace("|", "\\|")
            rows.append(f"| {name} | {field['type']} | {purpose} | {example} |")
        return "\n".join(rows)

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
            "final_status": summary["final_status"],
            "label_values": summary["label_values"],
            "fields": summary["fields"][:5],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
