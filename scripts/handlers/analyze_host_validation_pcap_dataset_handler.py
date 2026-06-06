from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.analyze_host_validation_cap_dataset_handler import (
    HostValidationCAPContentAnalysisHandler,
)
from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostValidationPCAPContentAnalysisResult:
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


class HostValidationPCAPContentAnalysisHandler(HostValidationCAPContentAnalysisHandler):
    FORMAT_NAME = "pcap"
    SUMMARY_JSON_FILE = "analysis-host-validation-pcap-summary.json"

    def analyze_and_generate_docs(self) -> HostValidationPCAPContentAnalysisResult:
        all_paths = self._extract_paths(self._read_source_json())
        if not all_paths:
            raise ValueError("No files found in sort-path-host-file.json for VALIDATION/pcap.")

        sampled_paths = self._select_sample_paths(all_paths)
        summary = self._build_summary(all_paths, sampled_paths)

        summary_json_path = self.temp_data_path / self.SUMMARY_JSON_FILE
        JsonDataManager(summary_json_path).write(summary)

        docs_ru_path = self.docs_ru_dir / "pcap.md"
        docs_en_path = self.docs_en_dir / "pcap.md"
        docs_ru_readme_path = self.docs_ru_dir / "README.md"
        docs_en_readme_path = self.docs_en_dir / "README.md"
        report_ru_path = self.report_ru_dir / "Task5(Analysis of host validation pcap dataset files)_report.md"
        report_en_path = self.report_en_dir / "Task5(Analysis of host validation pcap dataset files)_report.md"

        self._write_text_file(docs_ru_path, self._build_markdown(summary, "ru"))
        self._write_text_file(docs_en_path, self._build_markdown(summary, "en"))
        self._write_text_file(docs_ru_readme_path, self._build_readme(summary, "ru"))
        self._write_text_file(docs_en_readme_path, self._build_readme(summary, "en"))
        self._write_text_file(report_ru_path, self._build_report(summary, summary_json_path, "ru"))
        self._write_text_file(report_en_path, self._build_report(summary, summary_json_path, "en"))

        return HostValidationPCAPContentAnalysisResult(
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

    def _build_markdown(self, summary: dict[str, Any], language: str) -> str:
        text = super()._build_markdown(summary, language)
        replacements = {
            "# Анализ формата: cap": "# Анализ формата: pcap",
            "# Format Analysis: cap": "# Format Analysis: pcap",
            "`.cap`": "`.pcap`",
            "| Формат | cap |": "| Формат | pcap |",
            "| Format | cap |": "| Format | pcap |",
            "| Варианты расширения | .cap |": "| Варианты расширения | .pcap |",
            "| Extension variants | .cap |": "| Extension variants | .pcap |",
            "VALIDATION\\cap": "VALIDATION\\pcap",
            "analysis-host-validation-cap-summary.json": self.SUMMARY_JSON_FILE,
        }
        for source, target in replacements.items():
            text = text.replace(source, target)
        return text

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
            "pcap": (summary["final_status"], "pcap.md"),
        }
        rows = []
        for fmt, count in sorted(self._load_counts().items()):
            status, document = status_by_format.get(fmt, (pending, "-"))
            rows.append(f"| {fmt} | {count} | {no} | {yes} | {status} | {document} |")
        return f"{title} (Host VALIDATION)\n\n{header}|---|---:|---|---|---|---|\n" + "\n".join(rows) + "\n"

    def _build_report(self, summary: dict[str, Any], summary_json_path: Path, language: str) -> str:
        ru = language == "ru"
        title = (
            "# Отчёт по Task5: Analysis of host validation pcap dataset files"
            if ru
            else "# Task5 Report: Analysis of host validation pcap dataset files"
        )
        description = (
            f"Выполнен анализ `PATH_HOST_DATASETS_FILTER\\VALIDATION\\pcap` на основе "
            f"`{self.HOST_INPUT_JSON_FILE}`. Исходные датасеты не изменялись, обучение моделей не выполнялось."
            if ru
            else f"Analyzed `PATH_HOST_DATASETS_FILTER\\VALIDATION\\pcap` using `{self.HOST_INPUT_JSON_FILE}`. "
            "Source datasets were not modified, and no model training was performed."
        )
        return f"""{title}

## {'Описание задачи' if ru else 'Task Description'}
{description}

## {'Добавленные или изменённые файлы' if ru else 'Added or Changed Files'}
- `scripts/handlers/analyze_host_validation_pcap_dataset_handler.py`
- `manage.py`
- `temp_data/{self.SUMMARY_JSON_FILE}`
- `docs/ru/analysis-dataset/host/validation/pcap.md`
- `docs/en/analysis-dataset/host/validation/pcap.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task5(Analysis of host validation pcap dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task5(Analysis of host validation pcap dataset files)_report.md`

## {'Структура JSON' if ru else 'JSON Structure'}
`{self.HOST_INPUT_JSON_FILE}`: `role -> format -> list[path]`; bucket: `VALIDATION.pcap`.

## {'Логика анализа' if ru else 'Analysis Logic'}
{('Handler читает pcap global header и ограниченное число packet records; payload не изменяется и не сохраняется.' if ru else 'The handler reads the pcap global header and a limited number of packet records; payload is not modified or persisted.')}

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
        excerpt = {
            "format": summary["format"],
            "role": summary["role"],
            "scope": summary["scope"],
            "parsed_packets": summary["parsed_packets"],
            "ip_protocols": summary["ip_protocols"],
            "final_status": summary["final_status"],
        }
        return json.dumps(excerpt, ensure_ascii=False, indent=2)
