from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class HostSortedPathExportResult:
    """Результат экспорта путей отсортированных Host-датасетов."""

    json_file: str
    scanned_files_count: int
    grouped_paths: dict[str, dict[str, list[str]]]
    counts_by_role_and_format: dict[str, dict[str, int]]


class HostSortedPathExportHandler:
    """Сканирует PATH_HOST_DATASETS_FILTER и сохраняет пути в JSON по ролям/форматам."""

    ROLE_ORDER: tuple[str, ...] = ("TRAIN", "TEST", "VALIDATION")

    def __init__(
        self,
        host_datasets_filter_path: str | Path,
        temp_data_path: str | Path,
    ) -> None:
        self.host_datasets_filter_path_raw = str(host_datasets_filter_path).strip()
        self.host_datasets_filter_path = Path(self.host_datasets_filter_path_raw).expanduser()
        self.temp_data_path = Path(temp_data_path).expanduser()

    def export_paths(self) -> HostSortedPathExportResult:
        """Формирует sort-path-host-file.json из текущей структуры отсортированных Host-датасетов."""
        self._validate_source_root()

        grouped_paths: dict[str, dict[str, list[str]]] = {role: {} for role in self.ROLE_ORDER}
        scanned_files_count = 0

        for role in self.ROLE_ORDER:
            role_directory = self.host_datasets_filter_path / role
            if not role_directory.exists() or not role_directory.is_dir():
                continue

            grouped_paths[role] = self._scan_role_directory(role_directory)
            scanned_files_count += sum(len(paths) for paths in grouped_paths[role].values())

        counts_by_role_and_format = {
            role: {
                format_name: len(paths)
                for format_name, paths in grouped_paths[role].items()
            }
            for role in self.ROLE_ORDER
        }

        output_json_path = self.temp_data_path / "sort-path-host-file.json"
        JsonDataManager(output_json_path).write(grouped_paths)

        summary_payload: dict[str, Any] = {
            "json_file": str(output_json_path),
            "scanned_files_count": scanned_files_count,
            "counts_by_role_and_format": counts_by_role_and_format,
        }
        JsonDataManager(self.temp_data_path / "sort-path-host-file-summary.json").write(summary_payload)

        return HostSortedPathExportResult(
            json_file=str(output_json_path),
            scanned_files_count=scanned_files_count,
            grouped_paths=grouped_paths,
            counts_by_role_and_format=counts_by_role_and_format,
        )

    def _validate_source_root(self) -> None:
        """Проверяет, что директория с отсортированными Host-датасетами задана и существует."""
        if not self.host_datasets_filter_path_raw:
            raise ValueError(
                "Переменная PATH_HOST_DATASETS_FILTER не задана. "
                "Укажите путь к директории отсортированных Host-датасетов."
            )

        if not self.host_datasets_filter_path.exists():
            raise FileNotFoundError(
                f"Директория PATH_HOST_DATASETS_FILTER не найдена: {self.host_datasets_filter_path}"
            )

        if not self.host_datasets_filter_path.is_dir():
            raise NotADirectoryError(
                f"PATH_HOST_DATASETS_FILTER должен указывать на директорию: {self.host_datasets_filter_path}"
            )

    @staticmethod
    def _scan_role_directory(role_directory: Path) -> dict[str, list[str]]:
        """Сканирует файлы роли и группирует их по format-папкам."""
        role_grouped: dict[str, list[str]] = {}

        for format_directory in sorted(role_directory.iterdir(), key=lambda path: path.name.lower()):
            if not format_directory.is_dir():
                continue

            format_name = format_directory.name
            file_paths = [
                str(path.resolve())
                for path in sorted(format_directory.rglob("*"), key=lambda p: str(p).lower())
                if path.is_file()
            ]

            if file_paths:
                role_grouped[format_name] = file_paths

        return role_grouped
