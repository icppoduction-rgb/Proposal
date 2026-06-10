from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.host_analyze.analyze_host_test_netflow_day_dataset_handler import (
    HostTestNetflowDayContentAnalysisHandler,
)


@dataclass(frozen=True)
class HostValidationNetflowDayContentAnalysisResult:
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


class HostValidationNetflowDayContentAnalysisHandler(HostTestNetflowDayContentAnalysisHandler):
    ROLE_NAME = "VALIDATION"
    SUMMARY_JSON_FILE = "analysis-host-validation-netflow-day-summary.json"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = HostTestNetflowDayContentAnalysisHandler.DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = HostTestNetflowDayContentAnalysisHandler.DEFAULT_MAX_LINES_PER_FILE,
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

    def analyze_and_generate_docs(self) -> HostValidationNetflowDayContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for VALIDATION/netflow_day.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        self._write_json_file(summary_json_path, summary_payload)

        docs_ru_path = self.docs_ru_dir / "netflow_day.md"
        docs_en_path = self.docs_en_dir / "netflow_day.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task4(Analysis of host validation netflow_day dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task4(Analysis of host validation netflow_day dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_ru_markdown(summary_payload))
        self._write_text_file(docs_en_path, self._build_en_markdown(summary_payload))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary_payload, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary_payload, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary_payload, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary_payload, summary_json_path, "en"))

        return HostValidationNetflowDayContentAnalysisResult(
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

    def _build_ru_markdown(self, summary: dict[str, Any]) -> str:
        return (
            super()
            ._build_ru_markdown(summary)
            .replace("Host TEST", "Host VALIDATION")
            .replace("| Роли | TEST |", "| Роли | VALIDATION |")
        )

    def _build_en_markdown(self, summary: dict[str, Any]) -> str:
        return (
            super()
            ._build_en_markdown(summary)
            .replace("Host TEST", "Host VALIDATION")
            .replace("| Roles | TEST |", "| Roles | VALIDATION |")
        )

    def _build_readme(self, summary: dict[str, Any], language: str) -> str:
        title = (
            "# Анализ содержимого файлов датасетов"
            if language == "ru"
            else "# Dataset File Content Analysis"
        )
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
            "netflow_day": (summary["final_status"], "netflow_day.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task4: Analysis of host validation netflow_day dataset files"
            if ru
            else "# Task4 Report: Analysis of host validation netflow_day dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\VALIDATION\\netflow_day` на основе "
            f"`{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\VALIDATION\\netflow_day` using "
            f"`{self.HOST_INPUT_JSON_FILE}`. Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_validation_netflow_day_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/validation/netflow_day.md`
- `docs/en/analysis-dataset/host/validation/netflow_day.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/validation/Task4(Analysis of host validation netflow_day dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/validation/Task4(Analysis of host validation netflow_day dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.netflow_day`.

## {'Логика группировки путей' if ru else 'Path Grouping Logic'}
{('Handler анализирует все пути формата и читает только первые sample-строки огромных файлов.' if ru else 'The handler analyzes all paths for the format and reads only the first sample rows from huge files.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    def _load_counts(self) -> dict[str, int]:
        return self._load_host_test_format_counts()

    @staticmethod
    def _summary_json_excerpt(summary: dict[str, Any]) -> str:
        excerpt = {
            "format": summary["format"],
            "role": summary["role"],
            "scope": summary["scope"],
            "parsed_rows": summary["parsed_rows"],
            "protocol_counts_sample": summary["protocol_counts_sample"],
            "final_status": summary["final_status"],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)

    @staticmethod
    def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
