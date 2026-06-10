from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class HostFilterResult:
    """Результат фильтрации Host-датасетов."""

    path_json_file: str
    files_json_file: str
    log_file: str
    file_paths_by_role: dict[str, list[str]]
    files_by_role: dict[str, list[str]]
    kept_files_count: int
    excluded_files_count: int
    excluded_by_reason: dict[str, int]


class HostDatasetFilterHandler:
    """Обработчик этапа фильтрации Host-датасетов."""

    ROLE_ORDER: tuple[str, ...] = ("TRAIN", "TEST", "VALIDATION")

    DATASET_ROLE_MAP: dict[str, set[str]] = {
        "TRAIN": {"ADFA IDS", "LID-DS 2021", "Maintainable Log Dataset"},
        "TEST": {
            "Unified-Host-Network-Dataset -LANL",
            "ISOT-Cloud-IDS-Dataset",
            "Dynamic-Malware-Analysis-Dataset",
        },
        "VALIDATION": {
            "LID-DS 2019",
            "LANL Dataset",
            "Windows-Event-Log -OTRF-Security-Datasets",
        },
    }

    ADFA_ALLOWED_SUFFIXES: set[str] = {".txt", ".ghc", ".csv", ".netflow_ids", ".xml"}
    LID_DS_2021_ALLOWED_SUFFIXES: set[str] = {".sc", ".json"}
    LID_DS_2019_ALLOWED_SUFFIXES: set[str] = {".txt", ".csv"}
    OTRF_ALLOWED_SUFFIXES: set[str] = {".json", ".cap", ".pcap", ".pcapng"}
    ISOT_ALLOWED_SUFFIXES: set[str] = {".csv"}
    DYNAMIC_MALWARE_ALLOWED_SUFFIXES: set[str] = {".txt", ".json", ".bson", ".log"}

    def __init__(
        self,
        temp_data_path: str | Path,
        log_file_path: str | Path,
    ) -> None:
        self.temp_data_path = Path(temp_data_path).expanduser()
        self.log_file_path = Path(log_file_path).expanduser()
        self._logger = self._build_logger()

    def filter_and_save(self) -> HostFilterResult:
        """
        Читает исходные host JSON, выполняет фильтрацию и сохраняет:
        - filter_dataset-host-path-file.json
        - filter_dataset-host-file.json
        """
        source_paths = JsonDataManager(self.temp_data_path / "host-path-file.json").read(default={})
        source_files = JsonDataManager(self.temp_data_path / "host-file.json").read(default={})

        self._validate_source_json(source_paths, "host-path-file.json")
        self._validate_source_json(source_files, "host-file.json")

        source_file_names_by_role = self._normalize_files_by_role(source_files)

        file_paths_by_role_set: dict[str, set[str]] = self._init_role_sets()
        files_by_role_set: dict[str, set[str]] = self._init_role_sets()
        excluded_by_reason: dict[str, int] = {}

        kept_files_count = 0
        excluded_files_count = 0

        for role in self.ROLE_ORDER:
            role_items = source_paths.get(role, [])
            if not isinstance(role_items, list):
                raise ValueError(f"Поле роли '{role}' в host-path-file.json должно быть списком.")

            for raw_path in role_items:
                if not isinstance(raw_path, str):
                    excluded_files_count += 1
                    self._track_exclusion(
                        excluded_by_reason=excluded_by_reason,
                        file_path=str(raw_path),
                        reason="invalid_path_type",
                        role=role,
                        dataset_name="UNKNOWN",
                    )
                    continue

                file_path = Path(raw_path)
                dataset_name = self._extract_dataset_name(file_path)
                if dataset_name is None:
                    excluded_files_count += 1
                    self._track_exclusion(
                        excluded_by_reason=excluded_by_reason,
                        file_path=raw_path,
                        reason="dataset_name_not_detected",
                        role=role,
                        dataset_name="UNKNOWN",
                    )
                    continue

                if dataset_name not in self.DATASET_ROLE_MAP[role]:
                    excluded_files_count += 1
                    self._track_exclusion(
                        excluded_by_reason=excluded_by_reason,
                        file_path=raw_path,
                        reason="dataset_not_allowed_for_role",
                        role=role,
                        dataset_name=dataset_name,
                    )
                    continue

                is_allowed, reason = self._is_allowed_file(dataset_name=dataset_name, file_path=file_path)
                if not is_allowed:
                    excluded_files_count += 1
                    self._track_exclusion(
                        excluded_by_reason=excluded_by_reason,
                        file_path=raw_path,
                        reason=reason,
                        role=role,
                        dataset_name=dataset_name,
                    )
                    continue

                file_name = self._path_name(file_path)
                if file_name not in source_file_names_by_role[role]:
                    excluded_files_count += 1
                    self._track_exclusion(
                        excluded_by_reason=excluded_by_reason,
                        file_path=raw_path,
                        reason="file_name_not_present_in_host_file_json",
                        role=role,
                        dataset_name=dataset_name,
                    )
                    continue

                kept_files_count += 1
                file_paths_by_role_set[role].add(raw_path)
                files_by_role_set[role].add(file_name)

        file_paths_by_role = self._prepare_output(file_paths_by_role_set)
        files_by_role = self._prepare_output(files_by_role_set)

        filter_path_json = self.temp_data_path / "filter_dataset-host-path-file.json"
        filter_file_json = self.temp_data_path / "filter_dataset-host-file.json"

        JsonDataManager(filter_path_json).write(file_paths_by_role)
        JsonDataManager(filter_file_json).write(files_by_role)

        return HostFilterResult(
            path_json_file=str(filter_path_json),
            files_json_file=str(filter_file_json),
            log_file=str(self.log_file_path),
            file_paths_by_role=file_paths_by_role,
            files_by_role=files_by_role,
            kept_files_count=kept_files_count,
            excluded_files_count=excluded_files_count,
            excluded_by_reason=dict(sorted(excluded_by_reason.items())),
        )

    def _build_logger(self) -> logging.Logger:
        """Создаёт logger для записи исключённых файлов."""
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger("host_filter_logger")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # Важно очищать старые handlers, чтобы не дублировать строки лога.
        logger.handlers.clear()

        handler = logging.FileHandler(self.log_file_path, mode="w", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _track_exclusion(
        self,
        excluded_by_reason: dict[str, int],
        file_path: str,
        reason: str,
        role: str,
        dataset_name: str,
    ) -> None:
        """Учитывает исключение и пишет его в лог."""
        excluded_by_reason[reason] = excluded_by_reason.get(reason, 0) + 1
        self._logger.info(
            "dataset_type=HOST | role=%s | dataset=%s | reason=%s | path=%s",
            role,
            dataset_name,
            reason,
            file_path,
        )

    def _validate_source_json(self, data: dict[str, Any], file_name: str) -> None:
        """Проверяет структуру исходного JSON."""
        missing_roles = [role for role in self.ROLE_ORDER if role not in data]
        if missing_roles:
            roles_text = ", ".join(missing_roles)
            raise ValueError(
                f"В файле {file_name} отсутствуют обязательные роли: {roles_text}."
            )

    def _normalize_files_by_role(self, source_files: dict[str, Any]) -> dict[str, set[str]]:
        """Преобразует входные имена файлов в нормализованные множества по ролям."""
        normalized = self._init_role_sets()
        for role in self.ROLE_ORDER:
            role_items = source_files.get(role, [])
            if not isinstance(role_items, list):
                raise ValueError(f"Поле роли '{role}' в host-file.json должно быть списком.")
            normalized[role] = {str(item) for item in role_items if isinstance(item, str)}
        return normalized

    def _is_allowed_file(self, dataset_name: str, file_path: Path) -> tuple[bool, str]:
        """Проверяет, нужен ли файл для дальнейших этапов подготовки датасетов."""
        file_name = self._path_name(file_path)
        suffix = Path(file_name).suffix.lower()
        lower_path = f"/{self._normalize_path_text(file_path).lower().strip('/')}/"
        file_name_lower = file_name.lower()

        if file_name_lower.startswith("._"):
            return False, "macos_resource_fork_file"

        if dataset_name == "ADFA IDS":
            if suffix in self.ADFA_ALLOWED_SUFFIXES:
                return True, "ok"
            return False, f"unsupported_extension:{suffix or '<noext>'}"

        if dataset_name == "LID-DS 2021":
            if suffix in self.LID_DS_2021_ALLOWED_SUFFIXES:
                return True, "ok"
            return False, f"unsupported_extension:{suffix or '<noext>'}"

        if dataset_name == "Maintainable Log Dataset":
            if "/logs/" not in lower_path and "/alerts_csv/" not in lower_path and "/labels/" not in lower_path:
                return False, "non_telemetry_path_for_maintainable_dataset"
            if suffix in {".jpg", ".jpeg", ".png", ".svg", ".pdf", ".doc", ".docx", ".odt", ".xlsx"}:
                return False, f"unsupported_binary_or_document_extension:{suffix}"
            return True, "ok"

        if dataset_name == "LID-DS 2019":
            if suffix in self.LID_DS_2019_ALLOWED_SUFFIXES:
                return True, "ok"
            return False, f"unsupported_extension:{suffix or '<noext>'}"

        if dataset_name == "LANL Dataset":
            return True, "ok"

        if dataset_name == "Windows-Event-Log -OTRF-Security-Datasets":
            if suffix in self.OTRF_ALLOWED_SUFFIXES:
                return True, "ok"
            return False, f"unsupported_extension:{suffix or '<noext>'}"

        if dataset_name == "Unified-Host-Network-Dataset -LANL":
            return True, "ok"

        if dataset_name == "ISOT-Cloud-IDS-Dataset":
            if suffix in self.ISOT_ALLOWED_SUFFIXES:
                return True, "ok"
            return False, f"unsupported_extension:{suffix or '<noext>'}"

        if dataset_name == "Dynamic-Malware-Analysis-Dataset":
            if suffix in self.DYNAMIC_MALWARE_ALLOWED_SUFFIXES:
                return True, "ok"
            return False, f"unsupported_extension:{suffix or '<noext>'}"

        return False, "dataset_not_in_filter_strategy"

    @staticmethod
    def _extract_dataset_name(file_path: Path) -> str | None:
        """Извлекает имя датасета из полного пути."""
        parts = [
            part
            for part in re.split(r"[\\/]+", str(file_path))
            if part
        ]
        for index, part in enumerate(parts):
            if part.lower() == "host" and index + 2 < len(parts):
                return parts[index + 2]
        return None

    @staticmethod
    def _normalize_path_text(file_path: Path) -> str:
        """Возвращает путь с единым разделителем для OS-independent проверок."""
        return str(file_path).replace("\\", "/")

    @classmethod
    def _path_name(cls, file_path: Path) -> str:
        """Возвращает basename для путей с POSIX- или Windows-разделителями."""
        normalized_path = cls._normalize_path_text(file_path).rstrip("/")
        return normalized_path.rsplit("/", 1)[-1]

    @classmethod
    def _init_role_sets(cls) -> dict[str, set[str]]:
        """Создаёт пустую структуру ролей с множествами."""
        return {role: set() for role in cls.ROLE_ORDER}

    @classmethod
    def _prepare_output(cls, role_map: dict[str, set[str]]) -> dict[str, list[str]]:
        """Преобразует множества ролей в отсортированные списки для JSON."""
        return {role: sorted(role_map.get(role, set())) for role in cls.ROLE_ORDER}
