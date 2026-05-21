from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonDataManager:
    """Класс для безопасной и удобной работы с JSON-файлами."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def ensure_directory(self) -> None:
        """Создаёт директорию для файла, если она отсутствует."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        """Проверяет, существует ли JSON-файл."""
        return self.file_path.is_file()

    def create(
        self,
        initial_data: dict[str, Any] | None = None,
        overwrite: bool = False,
        indent: int = 2,
    ) -> None:
        """
        Создаёт JSON-файл.

        Если файл уже существует и overwrite=False, содержимое не изменяется.
        """
        if self.exists() and not overwrite:
            return

        self.write(initial_data or {}, indent=indent)

    def read(self, default: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Читает JSON-файл и возвращает словарь.

        Если файл отсутствует, возвращается значение default.
        """
        if not self.exists():
            return default.copy() if default is not None else {}

        with self.file_path.open("r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        if not isinstance(data, dict):
            raise ValueError(f"JSON в файле {self.file_path} должен быть объектом.")

        return data

    def write(self, data: dict[str, Any], indent: int = 2) -> None:
        """Полностью перезаписывает JSON-файл переданными данными."""
        if not isinstance(data, dict):
            raise TypeError("Для записи в JSON ожидается словарь (dict).")

        self.ensure_directory()
        with self.file_path.open("w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=indent)
            json_file.write("\n")

    def update(self, new_data: dict[str, Any], indent: int = 2) -> dict[str, Any]:
        """
        Обновляет существующий JSON данными верхнего уровня и возвращает результат.
        """
        if not isinstance(new_data, dict):
            raise TypeError("Для обновления JSON ожидается словарь (dict).")

        current_data = self.read(default={})
        current_data.update(new_data)
        self.write(current_data, indent=indent)
        return current_data
