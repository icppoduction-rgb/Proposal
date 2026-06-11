from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from config import (
    DOCS_EN_ANALYSIS_HOST_VALIDATION,
    DOCS_RU_ANALYSIS_HOST_VALIDATION,
    REPORTS_RU_STAGE_ONE_ANALYSIS_HOST_VALIDATION,
    REPORTS_EN_STAGE_ONE_ANALYSIS_HOST_VALIDATION
)
from scripts.handlers.host_analyze.analyze_host_test_wls_day_dataset_handler import (
    HostTestWLSDayContentAnalysisHandler,
)


@dataclass(frozen=True)
class HostValidationWLSDayContentAnalysisResult:
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


class HostValidationWLSDayContentAnalysisHandler(HostTestWLSDayContentAnalysisHandler):
    ROLE_NAME = "VALIDATION"
    SUMMARY_JSON_FILE = "analysis-host-validation-wls-day-summary.json"

    def __init__(
        self,
        temp_data_path: str | Path,
        project_root: str | Path,
        report_path: str | Path | None = None,
        max_files_per_format: int = HostTestWLSDayContentAnalysisHandler.DEFAULT_MAX_FILES_PER_FORMAT,
        max_lines_per_file: int = HostTestWLSDayContentAnalysisHandler.DEFAULT_MAX_LINES_PER_FILE,
    ) -> None:
        super().__init__(temp_data_path, project_root, max_files_per_format, max_lines_per_file)
        self.docs_ru_dir = f"{self.project_root}/{DOCS_RU_ANALYSIS_HOST_VALIDATION}"
        self.docs_en_dir = f"{self.project_root}/{DOCS_EN_ANALYSIS_HOST_VALIDATION}"
        self.report_ru_dir = f"{self.report_path}/{REPORTS_RU_STAGE_ONE_ANALYSIS_HOST_VALIDATION}"
        self.report_en_dir = f"{self.report_path}/{REPORTS_EN_STAGE_ONE_ANALYSIS_HOST_VALIDATION}"

    def analyze_and_generate_docs(self) -> HostValidationWLSDayContentAnalysisResult:
        role_to_formats = self._read_source_json()
        all_paths = self._extract_paths(role_to_formats)
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for VALIDATION/wls_day.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary_payload = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        self._write_json_file(summary_json_path, summary_payload)

        docs_ru_path = self.docs_ru_dir / "wls_day.md"
        docs_en_path = self.docs_en_dir / "wls_day.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task8(Analysis of host validation wls_day dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task8(Analysis of host validation wls_day dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary_payload, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary_payload, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary_payload, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary_payload, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary_payload, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary_payload, summary_json_path, "en"))

        return HostValidationWLSDayContentAnalysisResult(
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

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        return (
            super()
            ._build_markdown(summary, language)
            .replace("Host TEST", "Host VALIDATION")
            .replace("| Roles | TEST |", "| Roles | VALIDATION |")
            .replace("| Роли | TEST |", "| Роли | VALIDATION |")
            .replace("\\host\\TEST\\", "\\host\\VALIDATION\\")
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
            "txt": (self._load_optional_status("analysis-host-validation-txt-summary.json"), "txt.md"),
            "wls_day": (summary["final_status"], "wls_day.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_host_test_format_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task8: Analysis of host validation wls_day dataset files"
            if ru
            else "# Task8 Report: Analysis of host validation wls_day dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\VALIDATION\\wls_day` на основе "
            f"`{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\VALIDATION\\wls_day` using `{self.HOST_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_validation_wls_day_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/validation/wls_day.md`
- `docs/en/analysis-dataset/host/validation/wls_day.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `PATH_REPORT/ru/stage-one/analysis-dataset/host/validation/Task8(Analysis of host validation wls_day dataset files)_report.md`
- `PATH_REPORT/en/stage-one/analysis-dataset/host/validation/Task8(Analysis of host validation wls_day dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.wls_day`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler анализирует все 3 файла и читает ограниченное число JSON Lines записей на файл.' if ru else 'The handler analyzes all 3 files and reads a limited number of JSON Lines records per file.')}

## {'Пример итогового JSON' if ru else 'Result JSON Example'}
```json
{self._summary_json_excerpt(summary)}
```

## {'Результат' if ru else 'Result'}
{('Создан' if ru else 'Created')} summary `{summary_json_path}`. {('Итоговый статус' if ru else 'Final status')}: `{summary['final_status']}`.
"""

    @staticmethod
    def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
