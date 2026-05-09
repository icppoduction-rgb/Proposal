from pathlib import Path


def collect_dataset_files(root_dir: str | Path) -> dict[str, dict[str, list[str]]]:
    """
    Формирует словарь с путями к файлам внутри структуры datasets.

    Ожидаемая структура:

    datasets/
        dns/
            TRAIN/
            VALIDATION/
            TEST/
        host/
            TRAIN/
            VALIDATION/
            TEST/
            EXPERIMENTS/
    """

    root_path = Path(root_dir)

    if not root_path.exists():
        raise FileNotFoundError(f"Директория не найдена: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"Путь не является директорией: {root_path}")

    result: dict[str, dict[str, list[str]]] = {}

    for dataset_type_dir in root_path.iterdir():
        if not dataset_type_dir.is_dir():
            continue

        dataset_type = dataset_type_dir.name
        result[dataset_type] = {}

        for category_dir in dataset_type_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category = category_dir.name

            files = [
                str(file_path)
                for file_path in category_dir.rglob("*")
                if file_path.is_file()
            ]

            result[dataset_type][category] = files

    return result

