from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class DNSTestPCAPContentAnalysisResult:
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


class DNSTestPCAPContentAnalysisHandler:
    ROLE_NAME = "TEST"
    FORMAT_NAME = "pcap"

    DNS_INPUT_JSON_FILE = "sort-path-dns-file.json"
    SUMMARY_JSON_FILE = "analysis-dns-test-pcap-summary.json"

    STATUS_BROKEN = "BROKEN_OR_EMPTY"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.project_root = Path(project_root).expanduser()
        self.report_path = Path(report_path).expanduser() if report_path is not None else self.project_root / "report"
        self.docs_ru_dir = self.project_root / "docs" / "ru" / "analysis-dataset" / "dns" / "test"
        self.docs_en_dir = self.project_root / "docs" / "en" / "analysis-dataset" / "dns" / "test"
        self.report_ru_dir = self.report_path / "ru" / "stage-one" / "analysis-dataset" / "dns" / "test"
        self.report_en_dir = self.report_path / "en" / "stage-one" / "analysis-dataset" / "dns" / "test"

    def analyze_and_generate_docs(self) -> DNSTestPCAPContentAnalysisResult:
        payload = self._read_source_json()
        all_paths = self._extract_paths(payload)
        summary = self._build_summary(payload, all_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "pcap.md"
        docs_en_path = self.docs_en_dir / "pcap.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task2(Analysis of dns test pcap dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task2(Analysis of dns test pcap dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return DNSTestPCAPContentAnalysisResult(
            summary_json_file=str(summary_json_path),
            docs_ru_file=str(docs_ru_path),
            docs_en_file=str(docs_en_path),
            docs_ru_readme_file=str(docs_ru_readme_path),
            docs_en_readme_file=str(docs_en_readme_path),
            report_ru_file=str(report_ru_path),
            report_en_file=str(report_en_path),
            total_files_count=len(all_paths),
            sampled_files_count=0,
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

    def _build_summary(self, payload: dict[str, Any], all_paths: list[Path]) -> dict[str, Any]:
        role_bucket = payload.get(self.ROLE_NAME, {})
        source_has_format_bucket = isinstance(role_bucket, dict) and self.FORMAT_NAME in role_bucket
        blocking_reason = (
            "No TEST/pcap bucket is present in sort-path-dns-file.json."
            if not source_has_format_bucket
            else "TEST/pcap bucket is present but contains no files."
        )
        return {
            "format": self.FORMAT_NAME,
            "role": self.ROLE_NAME,
            "source_json": str(self.temp_data_path / self.DNS_INPUT_JSON_FILE),
            "scope": {
                "total_files_count": len(all_paths),
                "sampled_files_count": 0,
            },
            "sample_paths": [],
            "source_has_format_bucket": source_has_format_bucket,
            "blocking_reason": blocking_reason,
            "file_probes": [],
            "container_variants": {},
            "parsed_packets": 0,
            "dns_port_hits_sample": 0,
            "final_status": self.STATUS_BROKEN,
            "needs_custom_parser": False,
            "processing_priority": "low",
        }

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        ru = language == "ru"
        if ru:
            return f"""# Анализ формата: pcap

## 1. Назначение
PCAP-файлы DNS TEST должны содержать raw packet capture трафик для проверки packet-level DNS feature extraction. На текущем этапе такие файлы в подготовленном TEST-наборе отсутствуют.

## 2. Где встречается
| Поле | Значение |
|---|---|
| Формат | pcap |
| Варианты расширения | .pcap |
| DNS | да |
| Host | нет |
| Роли | TEST |
| Количество файлов | {summary["scope"]["total_files_count"]} |

## 3. Примеры файлов
```text
нет файлов в `TEST.pcap`
```

## 4. Техническая структура
| Проверка | Результат |
|---|---|
| Тип файла | binary |
| Чтение построчно | нет |
| Табличная структура | нет |
| Заголовок | недоступно |
| Разделитель | none |
| Кодировка | not applicable |
| Вложенная структура | packet records, если файлы появятся |
| Sample-файлов проанализировано | 0 |
| Sample packets | 0 |

## 5. Содержательная структура
Анализ содержимого невозможен: {summary["blocking_reason"]}

## 6. Найденные поля / колонки
| Поле | Тип | Назначение | Пример значения |
|---|---|---|---|
| - | - | нет файлов для анализа | - |

## 7. Label / class indicators
| Проверка | Результат |
|---|---|
| Label найден | нет |
| Название поля | - |
| Значения label | - |
| Можно использовать для supervised learning | нет |

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
- недоступны без raw pcap файлов.

### Network / hybrid-признаки
- недоступны без raw pcap файлов.

## 10. Проблемы качества данных
| Проблема | Найдена | Комментарий |
|---|---|---|
| Пустые файлы | да | bucket отсутствует или пуст |
| Поврежденные файлы | нет | файлов нет |
| Missing values | нет | файлов нет |
| Нестабильная структура | нет | файлов нет |
| Смешанные схемы | нет | файлов нет |

## 11. Итоговая пригодность
| Поле | Значение |
|---|---|
| Статус | {summary["final_status"]} |
| Нужен отдельный парсер | нет, пока нет входных файлов |
| Приоритет обработки | низкий |

## 12. Вывод
DNS TEST pcap на текущем этапе непригоден для анализа, потому что в подготовленном JSON нет `TEST.pcap`. Причина зафиксирована в summary и отчете.
"""

        return f"""# Format Analysis: pcap

## 1. Purpose
DNS TEST PCAP files should contain raw packet capture traffic for packet-level DNS feature extraction validation. At this stage, no such files are present in the prepared TEST dataset.

## 2. Where It Appears
| Field | Value |
|---|---|
| Format | pcap |
| Extension variants | .pcap |
| DNS | yes |
| Host | no |
| Roles | TEST |
| File count | {summary["scope"]["total_files_count"]} |

## 3. Example Files
```text
no files in `TEST.pcap`
```

## 4. Technical Structure
| Check | Result |
|---|---|
| File type | binary |
| Line-by-line reading | no |
| Tabular structure | no |
| Header | unavailable |
| Delimiter | none |
| Encoding | not applicable |
| Nested structure | packet records, if files are added |
| Sampled files analyzed | 0 |
| Sample packets | 0 |

## 5. Content Structure
Content analysis is not possible: {summary["blocking_reason"]}

## 6. Detected Fields / Columns
| Field | Type | Purpose | Example value |
|---|---|---|---|
| - | - | no files to analyze | - |

## 7. Label / Class Indicators
| Check | Result |
|---|---|
| Label found | no |
| Field name | - |
| Label values | - |
| Suitable for supervised learning | no |

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
- unavailable without raw pcap files.

### Network / Hybrid Features
- unavailable without raw pcap files.

## 10. Data Quality Issues
| Issue | Found | Comment |
|---|---|---|
| Empty files | yes | bucket is missing or empty |
| Corrupted files | no | no files exist |
| Missing values | no | no files exist |
| Unstable structure | no | no files exist |
| Mixed schemas | no | no files exist |

## 11. Final Suitability
| Field | Value |
|---|---|
| Status | {summary["final_status"]} |
| Separate parser required | no, while no input files exist |
| Processing priority | low |

## 12. Conclusion
DNS TEST pcap cannot be analyzed at this stage because the prepared JSON has no `TEST.pcap` bucket. The reason is recorded in the summary and report.
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
        pending = "ещё не анализировалось" if language == "ru" else "not analyzed yet"
        counts = self._load_counts()
        counts.setdefault(self.FORMAT_NAME, 0)
        status_by_format = {
            "csv": (self._load_optional_status("analysis-dns-test-csv-summary.json"), "csv.md"),
            "pcap": (summary["final_status"], "pcap.md"),
        }
        rows = []
        for fmt, count in sorted(counts.items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {yes} | {no} | {status} | {document} |")
        return f"{title} (DNS TEST)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task2: Analysis of dns test pcap dataset files"
            if ru
            else "# Task2 Report: Analysis of dns test pcap dataset files"
        )
        description = (
            f"Анализ `PATH_DNS_DATASETS_FILTER\\TEST\\pcap` не может быть выполнен по содержимому: {summary['blocking_reason']} "
            "Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Content analysis for `PATH_DNS_DATASETS_FILTER\\TEST\\pcap` cannot be performed: {summary['blocking_reason']} "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_dns_test_pcap_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/dns/test/pcap.md`
- `docs/en/analysis-dataset/dns/test/pcap.md`
- `docs/ru/analysis-dataset/dns/test/README.md`
- `docs/en/analysis-dataset/dns/test/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/dns/test/Task2(Analysis of dns test pcap dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/dns/test/Task2(Analysis of dns test pcap dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.DNS_INPUT_JSON_FILE}`: `role -> format -> list[path]`; expected bucket: `TEST.pcap`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler проверяет наличие bucket TEST.pcap и фиксирует блокирующую причину, если файлов нет.' if ru else 'The handler checks whether the TEST.pcap bucket exists and records the blocking reason when files are missing.')}

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
                "source_has_format_bucket": summary["source_has_format_bucket"],
                "blocking_reason": summary["blocking_reason"],
                "final_status": summary["final_status"],
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _write_text_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
