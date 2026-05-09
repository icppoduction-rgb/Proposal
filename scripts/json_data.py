import json
from typing import Any
from pathlib import Path


class JsonData:
    """
    Класс для чтения и записи данных в JSON-файл.
    """

    def __init__(self, file_path: str | Path, encoding: str = "utf-8") -> None:
        self.file_path = Path(file_path)
        self.encoding = encoding

    # Метод для чтения json
    def read(self, default: Any = None) -> Any:
        """
        Читает данные из JSON-файла.

        Если файл не существует или пустой — возвращает default.
        """

        if not self.file_path.exists():
            return default

        if self.file_path.stat().st_size == 0:
            return default

        try:
            with self.file_path.open("r", encoding=self.encoding) as file:
                return json.load(file)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Файл содержит некорректный JSON: {self.file_path}"
            ) from error

    # Метод для записи
    def write(self, data: Any, indent: int = 4, ensure_ascii: bool = False) -> None:
        """
        Записывает данные в JSON-файл.

        Если директории не существует — создаёт её.
        """

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with self.file_path.open("w", encoding=self.encoding) as file:
            json.dump(
                data,
                file,
                indent=indent,
                ensure_ascii=ensure_ascii
            )

    # Метод обновления
    def update(self, new_data: dict) -> dict:
        """
        Обновляет JSON-файл новыми данными.

        Работает только если данные в файле являются словарём.
        """

        data = self.read(default={})

        if not isinstance(data, dict):
            raise TypeError("Метод update() работает только с JSON-объектами dict")

        data.update(new_data)
        self.write(data)

        return data

    # Метод удаления
    def delete(self) -> None:
        """
        Удаляет JSON-файл, если он существует.
        """

        if self.file_path.exists():
            self.file_path.unlink()

    def exists(self) -> bool:
        """
        Проверяет существование JSON-файла.
        """

        return self.file_path.exists()