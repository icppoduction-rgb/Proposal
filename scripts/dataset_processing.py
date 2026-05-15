from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.json_data import JsonData


PROCESSED_PATH_FILE_NAME = "dataset-processed-path.json"
PROCESSED_EXTENSIONS_FILE_NAME = "dataset-processed-extensions.json"

SELECTED_DATASETS: dict[str, set[str]] = {
    "dns": {
        "CIC-Bell-DNS-EXF-2021",
        "CIC-Bell-DNS-2021",
        "BCCC-CIC-Bell-DNS-2024",
        "Mendeley-DNS-Exfiltration-Dataset",
        "Kaggle DNS Tunneling Dataset",
    },
    "host": {
        "ADFA IDS",
        "LID-DS 2021",
        "Maintainable Log Dataset",
        "LID-DS 2019",
        "LANL Dataset",
        "Windows-Event-Log -OTRF-Security-Datasets",
        "Unified-Host-Network-Dataset -LANL",
        "ISOT-Cloud-IDS-Dataset",
        "Dynamic-Malware-Analysis-Dataset",
        "HDFS-Log-Dataset",
        "BGL Logs",
        "Syscall Dataset Generator",
        "COMIDDS",
    },
}


@dataclass(frozen=True)
class DatasetProcessingResult:
    """
    Хранит итог обработки датасетов для вывода в CLI и тестовой проверки.
    """

    selected_files: int
    excluded_files: int
    selected_extensions: list[str]
    directories_to_delete: list[Path]
    deleted_directories: list[Path]
    processed_path_file: Path
    processed_extensions_file: Path


def read_dataset_path_json(path_file: str | Path) -> dict[str, dict[str, list[str]]]:
    """
    Читает исходный JSON с путями датасетов и проверяет базовую структуру данных.
    """

    data = JsonData(path_file).read(default={})

    if not isinstance(data, dict):
        raise TypeError(f"JSON с путями датасетов должен быть объектом: {path_file}")

    for domain, splits in data.items():
        if not isinstance(domain, str) or not isinstance(splits, dict):
            raise TypeError("Ожидается структура {domain: {split: [paths...]}}")

        for split, paths in splits.items():
            if not isinstance(split, str) or not isinstance(paths, list):
                raise TypeError("Ожидается структура {domain: {split: [paths...]}}")

            if not all(isinstance(path, str) for path in paths):
                raise TypeError("Все пути датасетов в JSON должны быть строками")

    return data


def extract_dataset_name(file_path: str | Path, domain: str, split: str) -> str | None:
    """
    Извлекает имя датасета из пути формата datasets/<domain>/<split>/<dataset_name>/...
    """

    path = Path(file_path)
    parts = path.parts

    for index, part in enumerate(parts):
        if part == domain and index + 2 < len(parts) and parts[index + 1] == split:
            return parts[index + 2]

    for index, part in enumerate(parts):
        if part == "datasets" and index + 3 < len(parts):
            if parts[index + 1] == domain and parts[index + 2] == split:
                return parts[index + 3]

    return None


def filter_dataset_paths(
    dataset_paths: dict[str, dict[str, list[str]]],
    selected_datasets: dict[str, set[str]],
) -> tuple[dict[str, dict[str, list[str]]], int]:
    """
    Оставляет только пути, которые относятся к датасетам из утвержденной стратегии.
    """

    result: dict[str, dict[str, list[str]]] = {}
    excluded_files = 0

    for domain, splits in dataset_paths.items():
        allowed_names = selected_datasets.get(domain, set())
        result[domain] = {}

        for split, paths in splits.items():
            selected_paths: list[str] = []

            for file_path in paths:
                dataset_name = extract_dataset_name(file_path, domain=domain, split=split)

                if dataset_name in allowed_names:
                    selected_paths.append(file_path)
                else:
                    excluded_files += 1

            result[domain][split] = selected_paths

    return result, excluded_files


def collect_processed_extensions(
    processed_paths: dict[str, dict[str, list[str]]],
) -> dict[str, list[str]]:
    """
    Собирает расширения всех файлов, которые остались в выбранных датасетах.
    """

    extensions = {
        Path(file_path).suffix.lower()
        for splits in processed_paths.values()
        for paths in splits.values()
        for file_path in paths
        if Path(file_path).suffix
    }

    return {"extensions": sorted(extensions)}


def find_unselected_dataset_directories(
    datasets_root: str | Path,
    selected_datasets: dict[str, set[str]],
) -> list[Path]:
    """
    Находит директории датасетов, которых нет в whitelist и которые можно удалить целиком.
    """

    root_path = Path(datasets_root)

    if not root_path.exists():
        raise FileNotFoundError(f"Директория datasets не найдена: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"Путь datasets не является директорией: {root_path}")

    directories: list[Path] = []

    for domain_dir in root_path.iterdir():
        if not domain_dir.is_dir():
            continue

        allowed_names = selected_datasets.get(domain_dir.name, set())

        for split_dir in domain_dir.iterdir():
            if not split_dir.is_dir():
                continue

            for dataset_dir in split_dir.iterdir():
                if dataset_dir.is_dir() and dataset_dir.name not in allowed_names:
                    directories.append(dataset_dir)

    return sorted(directories)


def delete_dataset_directories(directories: list[Path], datasets_root: str | Path) -> list[Path]:
    """
    Безопасно удаляет только директории датасетов внутри datasets/<domain>/<split>/.
    """

    root_path = Path(datasets_root).resolve()
    deleted_directories: list[Path] = []

    for directory in directories:
        resolved_directory = directory.resolve()
        relative_path = resolved_directory.relative_to(root_path)

        if len(relative_path.parts) < 3:
            raise ValueError(f"Отказ от удаления слишком верхнеуровневого пути: {directory}")

        if not resolved_directory.is_dir():
            continue

        shutil.rmtree(resolved_directory)
        deleted_directories.append(directory)

    return deleted_directories


def build_processed_file_paths(source_path_file: str | Path) -> tuple[Path, Path]:
    """
    Формирует пути для итоговых JSON-файлов рядом с исходным dataset-path-data.json.
    """

    source_path = Path(source_path_file)
    output_dir = source_path.parent if source_path.parent != Path("") else Path("data-json")

    return (
        output_dir / PROCESSED_PATH_FILE_NAME,
        output_dir / PROCESSED_EXTENSIONS_FILE_NAME,
    )


def write_processed_dataset_json(
    processed_paths: dict[str, dict[str, list[str]]],
    processed_extensions: dict[str, list[str]],
    processed_path_file: str | Path,
    processed_extensions_file: str | Path,
) -> None:
    """
    Записывает итоговые JSON-файлы с выбранными путями и расширениями.
    """

    JsonData(processed_path_file).write(processed_paths)
    JsonData(processed_extensions_file).write(processed_extensions)


def process_datasets(
    datasets_root: str | Path,
    source_path_file: str | Path,
    *,
    dry_run: bool = False,
) -> DatasetProcessingResult:
    """
    Выполняет полный процесс выборки датасетов, записи JSON и удаления лишних директорий.
    """

    dataset_paths = read_dataset_path_json(source_path_file)
    processed_paths, excluded_files = filter_dataset_paths(
        dataset_paths=dataset_paths,
        selected_datasets=SELECTED_DATASETS,
    )
    processed_extensions = collect_processed_extensions(processed_paths)
    directories_to_delete = find_unselected_dataset_directories(
        datasets_root=datasets_root,
        selected_datasets=SELECTED_DATASETS,
    )
    processed_path_file, processed_extensions_file = build_processed_file_paths(source_path_file)

    deleted_directories: list[Path] = []

    if not dry_run:
        write_processed_dataset_json(
            processed_paths=processed_paths,
            processed_extensions=processed_extensions,
            processed_path_file=processed_path_file,
            processed_extensions_file=processed_extensions_file,
        )
        deleted_directories = delete_dataset_directories(
            directories=directories_to_delete,
            datasets_root=datasets_root,
        )

    selected_files = sum(
        len(paths)
        for splits in processed_paths.values()
        for paths in splits.values()
    )

    return DatasetProcessingResult(
        selected_files=selected_files,
        excluded_files=excluded_files,
        selected_extensions=processed_extensions["extensions"],
        directories_to_delete=directories_to_delete,
        deleted_directories=deleted_directories,
        processed_path_file=processed_path_file,
        processed_extensions_file=processed_extensions_file,
    )


def print_processing_result(result: DatasetProcessingResult, *, dry_run: bool) -> None:
    """
    Печатает краткий отчет о выбранных файлах, расширениях и удаляемых директориях.
    """

    mode = "DRY-RUN" if dry_run else "APPLY"

    print(f"Mode: {mode}")
    print(f"Selected files: {result.selected_files}")
    print(f"Excluded files: {result.excluded_files}")
    print(f"Selected extensions: {len(result.selected_extensions)}")
    print(f"Directories to delete: {len(result.directories_to_delete)}")

    for directory in result.directories_to_delete:
        print(f" - {directory}")

    if dry_run:
        print("JSON files were not written. Directories were not deleted.")
    else:
        print(f"Written: {result.processed_path_file}")
        print(f"Written: {result.processed_extensions_file}")
        print(f"Deleted directories: {len(result.deleted_directories)}")
