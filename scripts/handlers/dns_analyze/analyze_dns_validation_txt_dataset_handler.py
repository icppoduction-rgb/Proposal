from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class DNSValidationTXTContentAnalysisResult:
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
class DNSTXTProbe:
    path: str
    file_name: str
    file_size_bytes: int
    sampled_lines: int
    non_empty_lines: int
    blank_lines: int
    domain_like_lines: int
    class_hint: str
    parse_error: str | None


class DNSValidationTXTContentAnalysisHandler:
    ROLE_NAME = "VALIDATION"
    FORMAT_NAME = "txt"

    DEFAULT_MAX_FILES_PER_FORMAT = 30
    DEFAULT_MAX_LINES_PER_FILE = 5000

    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-dns-validation-txt-summary.json"

    STATUS_READY = "READY_FOR_FEATURE_EXTRACTION"
    STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
    STATUS_BROKEN = "BROKEN_OR_EMPTY"

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
        self.max_lines_per_file = max(1, max_lines_per_file)
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "dns" / "validation"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "dns" / "validation"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "dns" / "validation"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "dns" / "validation"

    def analyze_and_generate_docs(self) -> DNSValidationTXTContentAnalysisResult:
        all_paths = self._extract_paths(self._read_source_json())
        if not all_paths:
            raise ValueError("No files found in sort-path-dns-file.json for VALIDATION/txt.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "txt.md"
        docs_en_path = self.docs_en_dir / "txt.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task2(Analysis of dns validation txt dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task2(Analysis of dns validation txt dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return DNSValidationTXTContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=len(sampled_paths),
            status=str(summary["final_status"]),
        )

    def _read_source_json(self) -> dict[str, Any]:
        source_json_path = self.temp_data_path / self.DNS_INPUT_JSON_FILE
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
            raise ValueError(f"Role '{self.ROLE_NAME}' format '{self.FORMAT_NAME}' must be a list.")
        return sorted(
            [Path(str(raw_path)).expanduser() for raw_path in format_bucket if isinstance(raw_path, str)],
            key=lambda path: str(path).lower(),
        )

    def _select_sample_paths(self, all_paths: list[Path]) -> list[Path]:
        return all_paths[: self.max_files_per_format]

    def _build_summary(self, all_paths: list[Path], sampled_paths: list[Path]) -> dict[str, Any]:
        probes: list[DNSTXTProbe] = []
        class_hints: Counter[str] = Counter()
        parse_errors: Counter[str] = Counter()
        examples: list[str] = []

        for path in sampled_paths:
            probe, file_examples = self._probe_txt(path)
            probes.append(probe)
            class_hints[probe.class_hint] += 1
            examples.extend(file_examples)
            if probe.parse_error:
                parse_errors[probe.parse_error] += 1

        total_non_empty = sum(probe.non_empty_lines for probe in probes)
        total_domain_like = sum(probe.domain_like_lines for probe in probes)
        total_blank = sum(probe.blank_lines for probe in probes)
        final_status = (
            self.STATUS_BROKEN
            if total_non_empty == 0
            else self.STATUS_PARTIAL
            if parse_errors or total_domain_like < total_non_empty
            else self.STATUS_READY
        )

        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.DNS_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": len(sampled_paths),
                "max_files_per_format": self.max_files_per_format,
                "max_lines_per_file": self.max_lines_per_file,
            },
            "sample_paths": [str(path) for path in sampled_paths],
            "file_probes": [probe.__dict__ for probe in probes],
            "class_hints": dict(class_hints.most_common()),
            "sample_values": examples[:20],
            "total_non_empty_lines_sample": total_non_empty,
            "total_domain_like_lines_sample": total_domain_like,
            "total_blank_lines_sample": total_blank,
            "parse_errors": dict(parse_errors),
            "final_status": final_status,
            "needs_custom_parser": False,
            "processing_priority": "medium",
        }

    def _probe_txt(self, path: Path) -> tuple[DNSTXTProbe, list[str]]:
        if not path.exists():
            return DNSTXTProbe(str(path), path.name, 0, 0, 0, 0, 0, "unknown", "file_not_found"), []
        file_size = path.stat().st_size
        examples: list[str] = []
        sampled_lines = 0
        blank_lines = 0
        non_empty_lines = 0
        domain_like_lines = 0
        try:
            with path.open("r", encoding="utf-8", errors="replace") as stream:
                for index, line in enumerate(stream):
                    if index >= self.max_lines_per_file:
                        break
                    sampled_lines += 1
                    value = line.strip()
                    if not value:
                        blank_lines += 1
                        continue
                    non_empty_lines += 1
                    if self._is_domain_like(value):
                        domain_like_lines += 1
                    if len(examples) < 5:
                        examples.append(value)
        except OSError as error:
            return DNSTXTProbe(
                str(path), path.name, file_size, sampled_lines, non_empty_lines, blank_lines, domain_like_lines,
                self._class_hint(path), str(error),
            ), examples

        return DNSTXTProbe(
            path=str(path),
            file_name=path.name,
            file_size_bytes=file_size,
            sampled_lines=sampled_lines,
            non_empty_lines=non_empty_lines,
            blank_lines=blank_lines,
            domain_like_lines=domain_like_lines,
            class_hint=self._class_hint(path),
            parse_error=None,
        ), examples

    @staticmethod
    def _class_hint(path: Path) -> str:
        lower_name = path.name.lower()
        if "benign" in lower_name:
            return "benign"
        if "malware" in lower_name:
            return "malware"
        if "attack" in lower_name:
            return "attack"
        return "unknown"

    @staticmethod
    def _is_domain_like(value: str) -> bool:
        if " " in value or "/" in value or "." not in value:
            return False
        labels = value.rstrip(".").split(".")
        return all(label and all(ch.isalnum() or ch == "-" for ch in label) for label in labels)

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        examples = "\n".join(summary["sample_paths"])
        values = "\n".join(summary["sample_values"][:10])
        classes = ", ".join(f"{key}: {value}" for key, value in summary["class_hints"].items())
        parse_error_count = sum(summary["parse_errors"].values())

        if ru:
            return f"""# Анализ формата: txt

## 1. Назначение
TXT-файлы DNS VALIDATION содержат доменные списки для проверки DNS/domain feature extraction, enrichment и validation-сценариев без packet parsing.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | txt |
| Варианты расширения | .txt |
| DNS | да |
| Host | нет |
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
| Табличная структура | нет |
| Заголовок | нет |
| Разделитель | newline |
| Кодировка | utf-8-compatible |
| Вложенная структура | нет |
| Sample-файлов проанализировано | {summary["scope"]["sampled_files_count"]} |
| Sample lines | {summary["total_non_empty_lines_sample"]} |

## 5. Содержательная структура
Файлы являются domain-list: одна доменная запись на строку. Class hints из имен файлов: {classes}. В sample domain-like строк: {summary["total_domain_like_lines_sample"]}.

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| domain | domain | доменное имя | {summary["sample_values"][0] if summary["sample_values"] else ""} |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | частично |
| Название поля | имя файла / class_hint |
| Значения label | {", ".join(summary["class_hints"].keys())} |
| Можно использовать для supervised learning | частично, только после явного назначения класса |

## 8. Временные признаки
| Проверка | Результат |
|---|---|
| Timestamp найден | нет |
| Название поля | - |
| Формат времени | - |
| Можно строить sequence | нет |
| Можно применять sliding window | нет |

## 9. Потенциальные признаки для feature extraction
### DNS-признаки
- длина домена и поддомена;
- количество labels;
- TLD/SLD;
- entropy и character composition;
- domain reputation/enrichment признаки.

### Network / hybrid-признаки
- join с pcap-derived DNS queries;
- проверка пересечений с allow/block lists.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | {"да" if summary["total_non_empty_lines_sample"] == 0 else "нет"} | non-empty lines в sample: {summary["total_non_empty_lines_sample"]} |
| Поврежденные файлы | {"да" if parse_error_count else "нет"} | parse errors: {parse_error_count} |
| Missing values | {"да" if summary["total_blank_lines_sample"] else "нет"} | blank lines в sample: {summary["total_blank_lines_sample"]} |
| Нестабильная структура | нет | newline-separated domain list |
| Смешанные схемы | нет | все sample-строки domain-like |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет |
| Приоритет обработки | средний |

## 12. Вывод
DNS VALIDATION txt готов к feature extraction как набор доменных списков; для supervised evaluation нужно явно закрепить семантику `unknown` списков.
"""

        return f"""# Format Analysis: txt

## 1. Purpose
DNS VALIDATION TXT files contain domain lists for DNS/domain feature extraction, enrichment, and validation scenarios without packet parsing.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | txt |
| Extension variants | .txt |
| DNS | yes |
| Host | no |
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
| Tabular structure | no |
| Header | no |
| Delimiter | newline |
| Encoding | utf-8-compatible |
| Nested structure | no |
| Sampled files analyzed | {summary["scope"]["sampled_files_count"]} |
| Sample lines | {summary["total_non_empty_lines_sample"]} |

## 5. Content Structure
Files are domain lists: one domain entry per line. Class hints from file names: {classes}. Domain-like lines in sample: {summary["total_domain_like_lines_sample"]}.

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| domain | domain | domain name | {summary["sample_values"][0] if summary["sample_values"] else ""} |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | partial |
| Field name | file name / class_hint |
| Label values | {", ".join(summary["class_hints"].keys())} |
| Suitable for supervised learning | partial, only after explicitly assigning class semantics |

## 8. Time Features
| Check | Result |
|---|---|
| Timestamp found | no |
| Field name | - |
| Time format | - |
| Can build sequences | no |
| Can apply sliding windows | no |

## 9. Potential Feature Extraction
### DNS Features
- domain and subdomain length;
- label count;
- TLD/SLD;
- entropy and character composition;
- domain reputation/enrichment features.

### Network / Hybrid Features
- join with pcap-derived DNS queries;
- allow/block list intersection checks.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | {"yes" if summary["total_non_empty_lines_sample"] == 0 else "no"} | non-empty lines in sample: {summary["total_non_empty_lines_sample"]} |
| Corrupted files | {"yes" if parse_error_count else "no"} | parse errors: {parse_error_count} |
| Missing values | {"yes" if summary["total_blank_lines_sample"] else "no"} | blank lines in sample: {summary["total_blank_lines_sample"]} |
| Unstable structure | no | newline-separated domain list |
| Mixed schemas | no | all sampled rows are domain-like |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no |
| Processing priority | medium |

## 12. Conclusion
DNS VALIDATION txt is ready for feature extraction as domain lists; supervised evaluation requires explicit semantics for `unknown` lists.
"""

    def _build_readme(self, summary: dict[str, Any], language: str) -> str:
        title = "# Анализ содержимого файлов датасетов" if language == "ru" else "# Dataset File Content Analysis"
        header = (
            "| Формат | Количество файлов | DNS | Host | Статус | Документ |\n"
            if language == "ru"
            else "| Format | File count | DNS | Host | Status | Document |\n"
        )
        yes = "да" if language == "ru" else "yes"
        no = "нет" if language == "ru" else "no"
        status_by_format = {
            "pcap": (self._load_optional_status("analysis-dns-validation-pcap-summary.json"), "pcap.md"),
            "txt": (summary["final_status"], "txt.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, ("-", "-"))
            rows.append(f"| {fmt} | {count} | {yes} | {no} | {status} | {document} |")
        return f"{title} (DNS VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task2: Analysis of dns validation txt dataset files"
            if ru
            else "# Task2 Report: Analysis of dns validation txt dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_DNS_DATASETS_FILTER\\VALIDATION\\txt` на основе `{self.DNS_INPUT_JSON_FILE}`. "
            "Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_DNS_DATASETS_FILTER\\VALIDATION\\txt` using `{self.DNS_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_dns_validation_txt_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/dns/validation/txt.md`
- `docs/en/analysis-dataset/dns/validation/txt.md`
- `docs/ru/analysis-dataset/dns/validation/README.md`
- `docs/en/analysis-dataset/dns/validation/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/dns/validation/Task2(Analysis of dns validation txt dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/dns/validation/Task2(Analysis of dns validation txt dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.DNS_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.txt`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler читает ограниченную выборку строк, проверяет domain-like структуру и class hints из имен файлов.' if ru else 'The handler reads a limited row sample, checks domain-like structure, and extracts class hints from file names.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_counts(self) -> dict[str, int]:
        payload = JsonDataManager(self.temp_data_path / self.DNS_INPUT_JSON_FILE).read(default={})
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
                "class_hints": summary["class_hints"],
                "total_non_empty_lines_sample": summary["total_non_empty_lines_sample"],
                "total_domain_like_lines_sample": summary["total_domain_like_lines_sample"],
                "final_status": summary["final_status"],
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
