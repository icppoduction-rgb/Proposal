from pathlib import Path

try:
    from rich.console import Console
except ModuleNotFoundError:
    class Console:
        def print(self, *objects: object, **kwargs: object) -> None:
            print(*objects)

from scripts.json_data import JsonData
from scripts.workdatasets.read_format import FileFormatReader


console = Console()


# Функция чтения файлов датасетов
def read_file_dataset(data: list[str], path_log_data: str, path_dataset_new: str) -> None:
    """
    :param data:
    :param path_log_data:
    :param path_dataset_new:
    """

    reader = FileFormatReader(log_path=f"{path_log_data}/conversion-dns-train.log")
    target_dir = Path(path_dataset_new)

    for path in data:

        console.print(f"==> [bold yellow]{path}[/bold yellow]")

        source_name = Path(path).name.split(".", maxsplit=1)[0]
        path_new_file = target_dir / f"{source_name}.json"

        result = reader.read(path)

        json_data = JsonData(path_new_file)

        json_data.write(result)


# Функция преобразования
def convertion(
        dns_key: str,
        path_log_data: str,
        path_file_json_dataset: str,
        path_dataset_new_dns: str,
) -> None:
    """
    :param dns_key:
    :param path_log_data:
    :param path_file_json_dataset:
    :param path_dataset_new_dns:
    """
    console.print(f"DNS conversion: {dns_key} | {path_dataset_new_dns} | {path_file_json_dataset}")

    json_data = JsonData(path_file_json_dataset)


    read_file_dataset(
        data=json_data.read()["dns"][dns_key.upper()],
        path_log_data=path_log_data,
        path_dataset_new=str(Path(path_dataset_new_dns) / dns_key.upper())
    )


