from pathlib import Path
from scripts.json_data import JsonData


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



def collect_extensions(root_dir: str | Path) -> dict[str, list[str]]:
    root_path = Path(root_dir)

    extensions = {
        file_path.suffix.lower()
        for file_path in root_path.rglob("*")
        if file_path.is_file() and file_path.suffix
    }

    return {
        "extensions": sorted(extensions)
    }


# Функция осуществляет запись путей в json файл
def write_dataset_path(path_folder: str, path_file: str) -> None:

    result_dict_path = collect_dataset_files(path_folder)

    json_data = JsonData(path_file)

    json_data.write(result_dict_path)

# Функция осуществляет запись расширение файлов в json
def write_extensions(path_folder: str, path_file: str) -> None:

    result_dict_extensions = collect_extensions(path_folder)

    json_data = JsonData(path_file)

    json_data.write(result_dict_extensions)

