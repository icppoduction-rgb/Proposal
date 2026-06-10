from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from scripts.handlers.json_handler.json_data import JsonDataManager


@dataclass(frozen=True)
class DNSAnalysisResult:
    """Результат анализа DNS-датасетов и сохранения JSON-файлов."""

    path_json_file: str
    files_json_file: str
    paths_by_role: dict[str, list[str]]
    files_by_role: dict[str, list[str]]


class DNSDatasetHandler:
    """Обработчик первого этапа анализа DNS-датасетов."""

    ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
        "TRAIN": ("train", "training"),
        "TEST": ("test", "testing"),
        "VALIDATION": ("validation", "valid", "val", "dev", "eval"),
        "EXPERIMENTS": ("experiment", "experiments", "exp", "sandbox", "trial"),
    }

    def __init__(self, dns_datasets_path: str | Path, temp_data_path: str | Path) -> None:
        self.dns_datasets_path_raw = str(dns_datasets_path).strip()
        self.dns_datasets_path = Path(self.dns_datasets_path_raw).expanduser()
        self.temp_data_path = Path(temp_data_path).expanduser()

    def analyze_and_save(self) -> DNSAnalysisResult:
        """
        Сканирует DNS-датасеты, распределяет пути и файлы по ролям и
        сохраняет результат в `dns-path-file.json` и `dns-file.json`.
        """
        self._validate_dns_root_path()

        paths_by_role_set: dict[str, set[str]] = self._init_role_sets()
        files_by_role_set: dict[str, set[str]] = self._init_role_sets()

        for current_path, files in self._walk_dns_files():
            role = self._detect_role(current_path)

            for file_name in files:
                file_path = current_path / file_name
                paths_by_role_set[role].add(str(file_path))
                files_by_role_set[role].add(file_name)

        paths_by_role = self._prepare_output(paths_by_role_set)
        files_by_role = self._prepare_output(files_by_role_set)

        path_json_file = self.temp_data_path / "dns-path-file.json"
        files_json_file = self.temp_data_path / "dns-file.json"

        JsonDataManager(path_json_file).write(paths_by_role)
        JsonDataManager(files_json_file).write(files_by_role)

        return DNSAnalysisResult(
            path_json_file=str(path_json_file),
            files_json_file=str(files_json_file),
            paths_by_role=paths_by_role,
            files_by_role=files_by_role,
        )

    def _validate_dns_root_path(self) -> None:
        """Проверяет корректность директории DNS-датасетов."""
        if not self.dns_datasets_path_raw:
            raise ValueError(
                "Переменная PATH_DNS_DATASETS не задана. "
                "Укажите путь до DNS-датасетов в окружении."
            )

        if not self.dns_datasets_path.exists():
            raise FileNotFoundError(
                f"Директория DNS-датасетов не найдена: {self.dns_datasets_path}"
            )

        if not self.dns_datasets_path.is_dir():
            raise NotADirectoryError(
                f"PATH_DNS_DATASETS должен указывать на директорию: {self.dns_datasets_path}"
            )

    def _walk_dns_files(self) -> list[tuple[Path, list[str]]]:
        """Возвращает список директорий DNS-датасета, в которых есть файлы."""
        files_by_directory: dict[Path, list[str]] = {}

        for path in self.dns_datasets_path.rglob("*"):
            if not path.is_file():
                continue

            files_by_directory.setdefault(path.parent, []).append(path.name)

        return list(files_by_directory.items())

    def _detect_role(self, path: Path) -> str:
        """Определяет роль датасета по токенам в имени директорий."""
        path_tokens = self._tokenize(str(path).lower())

        for role, keywords in self.ROLE_KEYWORDS.items():
            if any(keyword in path_tokens for keyword in keywords):
                return role

        return "EXPERIMENTS"

    @staticmethod
    def _tokenize(value: str) -> set[str]:
        """Разбивает строку на токены для поиска ключевых слов роли."""
        return {token for token in re.split(r"[^a-z0-9]+", value) if token}

    @classmethod
    def _init_role_sets(cls) -> dict[str, set[str]]:
        """Создаёт пустую структуру ролей с множествами."""
        return {role: set() for role in cls.ROLE_KEYWORDS}

    @classmethod
    def _prepare_output(cls, role_map: dict[str, set[str]]) -> dict[str, list[str]]:
        """Преобразует множества ролей в отсортированные списки для JSON."""
        return {
            role: sorted(role_map.get(role, set()))
            for role in cls.ROLE_KEYWORDS
        }
