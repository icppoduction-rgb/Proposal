from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonDataManager


@dataclass(frozen=True)
class DNSDatasetSortResult:
    """Результат сортировки DNS-датасетов по форматам файлов."""

    sorted_root_path: str
    summary_json_file: str
    created_links_count: int
    copied_files_count: int
    skipped_existing_count: int
    missing_source_count: int
    name_mismatch_count: int
    files_by_role_and_format: dict[str, dict[str, int]]


class DNSDatasetSortHandler:
    """Сортирует DNS-файлы по ролям и форматам на основе dns-path/file JSON."""

    ROLE_ORDER: tuple[str, ...] = ("TRAIN", "TEST", "VALIDATION", "EXPERIMENTS")

    def __init__(
        self,
        temp_data_path: str | Path,
        dns_datasets_filter_path: str | Path,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.dns_datasets_filter_path_raw = str(dns_datasets_filter_path).strip()
        self.dns_datasets_filter_path = Path(self.dns_datasets_filter_path_raw).expanduser()

    def sort_and_prepare(self) -> DNSDatasetSortResult:
        """
        Читает dns-path-file.json и dns-file.json и формирует структуру:
        PATH_DNS_DATASETS_FILTER/<ROLE>/<format>/...
        """
        self._validate_output_root()

        source_paths_data = JsonDataManager(self.temp_data_path / "dns-path-file.json").read(default={})
        source_files_data = JsonDataManager(self.temp_data_path / "dns-file.json").read(default={})

        self._validate_source_json(source_paths_data, "dns-path-file.json")
        self._validate_source_json(source_files_data, "dns-file.json")

        names_by_role = self._normalize_file_names(source_files_data)
        paths_by_role = self._normalize_file_paths(source_paths_data)

        self._create_base_role_directories()

        created_links_count = 0
        copied_files_count = 0
        skipped_existing_count = 0
        missing_source_count = 0
        name_mismatch_count = 0

        files_by_role_and_format: dict[str, dict[str, int]] = {
            role: {} for role in self.ROLE_ORDER
        }

        for role in self.ROLE_ORDER:
            role_paths = paths_by_role[role]
            role_names = names_by_role[role]

            for source_path in role_paths:
                source_name = source_path.name

                if source_name not in role_names:
                    name_mismatch_count += 1

                if not source_path.is_file():
                    missing_source_count += 1
                    continue

                format_group = self._detect_format_group(source_name)
                role_dir = self.dns_datasets_filter_path / role / format_group
                role_dir.mkdir(parents=True, exist_ok=True)

                destination_path = self._build_destination_path(role_dir=role_dir, source_path=source_path)
                if destination_path.exists() and self._is_same_file(destination_path, source_path):
                    skipped_existing_count += 1
                else:
                    created_as_link = self._materialize_file(source_path=source_path, destination_path=destination_path)
                    if created_as_link:
                        created_links_count += 1
                    else:
                        copied_files_count += 1

                current_count = files_by_role_and_format[role].get(format_group, 0)
                files_by_role_and_format[role][format_group] = current_count + 1

        files_by_role_and_format = {
            role: dict(sorted(files_by_role_and_format[role].items()))
            for role in self.ROLE_ORDER
        }

        summary_json_path = self.temp_data_path / "sort-dns-format-summary.json"
        summary_payload: dict[str, Any] = {
            "sorted_root_path": str(self.dns_datasets_filter_path),
            "created_links_count": created_links_count,
            "copied_files_count": copied_files_count,
            "skipped_existing_count": skipped_existing_count,
            "missing_source_count": missing_source_count,
            "name_mismatch_count": name_mismatch_count,
            "files_by_role_and_format": files_by_role_and_format,
        }
        JsonDataManager(summary_json_path).write(summary_payload)

        return DNSDatasetSortResult(
            sorted_root_path=str(self.dns_datasets_filter_path),
            summary_json_file=str(summary_json_path),
            created_links_count=created_links_count,
            copied_files_count=copied_files_count,
            skipped_existing_count=skipped_existing_count,
            missing_source_count=missing_source_count,
            name_mismatch_count=name_mismatch_count,
            files_by_role_and_format=files_by_role_and_format,
        )

    def _validate_output_root(self) -> None:
        """Проверяет корректность целевой директории сортировки."""
        if not self.dns_datasets_filter_path_raw:
            raise ValueError(
                "Переменная PATH_DNS_DATASETS_FILTER не задана. "
                "Укажите путь для сортировки DNS-датасетов."
            )

        self.dns_datasets_filter_path.mkdir(parents=True, exist_ok=True)
        if not self.dns_datasets_filter_path.is_dir():
            raise NotADirectoryError(
                f"PATH_DNS_DATASETS_FILTER должен указывать на директорию: {self.dns_datasets_filter_path}"
            )

    def _create_base_role_directories(self) -> None:
        """Создаёт обязательные разделы TRAIN/TEST/VALIDATION/EXPERIMENTS."""
        for role in self.ROLE_ORDER:
            (self.dns_datasets_filter_path / role).mkdir(parents=True, exist_ok=True)

    @classmethod
    def _validate_source_json(cls, data: dict[str, Any], file_name: str) -> None:
        """Проверяет, что входной JSON содержит все обязательные роли."""
        missing_roles = [role for role in cls.ROLE_ORDER if role not in data]
        if missing_roles:
            roles_text = ", ".join(missing_roles)
            raise ValueError(f"В файле {file_name} отсутствуют обязательные роли: {roles_text}.")

    @classmethod
    def _normalize_file_names(cls, source_files_data: dict[str, Any]) -> dict[str, set[str]]:
        """Нормализует имена файлов из dns-file.json."""
        normalized: dict[str, set[str]] = {role: set() for role in cls.ROLE_ORDER}
        for role in cls.ROLE_ORDER:
            role_items = source_files_data.get(role, [])
            if not isinstance(role_items, list):
                raise ValueError(f"Поле роли '{role}' в dns-file.json должно быть списком.")
            normalized[role] = {str(item) for item in role_items if isinstance(item, str)}
        return normalized

    @classmethod
    def _normalize_file_paths(cls, source_paths_data: dict[str, Any]) -> dict[str, list[Path]]:
        """Нормализует пути из dns-path-file.json."""
        normalized: dict[str, list[Path]] = {role: [] for role in cls.ROLE_ORDER}
        for role in cls.ROLE_ORDER:
            role_items = source_paths_data.get(role, [])
            if not isinstance(role_items, list):
                raise ValueError(f"Поле роли '{role}' в dns-path-file.json должно быть списком.")
            normalized[role] = [Path(str(item)).expanduser() for item in role_items if isinstance(item, str)]
        return normalized

    @staticmethod
    def _detect_format_group(file_name: str) -> str:
        """Определяет форматную группу DNS-файла по имени."""
        lower_name = file_name.lower()
        if lower_name.endswith(".pcap.csv"):
            return "pcap.csv"
        if lower_name.endswith(".pcap"):
            return "pcap"
        if lower_name.endswith(".csv"):
            return "csv"
        if lower_name.endswith(".txt"):
            return "txt"

        suffix = Path(lower_name).suffix.lstrip(".")
        if suffix:
            return suffix
        return lower_name

    @staticmethod
    def _destination_name_with_hash(source_path: Path) -> str:
        """Строит уникальное имя файла на основе исходного пути."""
        digest = hashlib.sha1(str(source_path).encode("utf-8")).hexdigest()[:10]
        source_name = source_path.name

        if "." not in source_name:
            return f"{source_name}__{digest}"

        stem, suffix = source_name.rsplit(".", 1)
        return f"{stem}__{digest}.{suffix}"

    @classmethod
    def _build_destination_path(cls, role_dir: Path, source_path: Path) -> Path:
        """Определяет путь назначения, избегая перезаписи коллизий имён."""
        candidate = role_dir / source_path.name

        if not candidate.exists():
            return candidate

        if cls._is_same_file(candidate, source_path):
            return candidate

        hashed_name = cls._destination_name_with_hash(source_path)
        candidate_hashed = role_dir / hashed_name

        if not candidate_hashed.exists():
            return candidate_hashed

        if cls._is_same_file(candidate_hashed, source_path):
            return candidate_hashed

        counter = 2
        while True:
            fallback_name = f"{Path(hashed_name).stem}__{counter}{Path(hashed_name).suffix}"
            fallback_candidate = role_dir / fallback_name
            if not fallback_candidate.exists() or cls._is_same_file(fallback_candidate, source_path):
                return fallback_candidate
            counter += 1

    @staticmethod
    def _is_same_file(first_path: Path, second_path: Path) -> bool:
        """Проверяет, ссылаются ли два пути на один и тот же файл."""
        try:
            return first_path.samefile(second_path)
        except OSError:
            return False

    @staticmethod
    def _materialize_file(source_path: Path, destination_path: Path) -> bool:
        """
        Создаёт файл в целевой директории:
        - сначала hardlink (без дублирования данных),
        - при ошибке fallback на copy2.

        Возвращает True, если создан hardlink, иначе False (копия).
        """
        if destination_path.exists():
            return True

        try:
            os.link(source_path, destination_path)
            return True
        except OSError:
            shutil.copy2(source_path, destination_path)
            return False
