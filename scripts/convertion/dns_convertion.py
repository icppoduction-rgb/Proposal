from rich.console import Console

from scripts.json_data import JsonData
from scripts.workdatasets.read_format import FileFormatReader


console = Console()


# Функция чтения файлов датасетов
def read_file_dataset(data: dict, path_log_data: str, path_dataset_new: str):
    """
    :param data:
    :param path_log_data:
    :param path_dataset_new:
    """

    print()

    reader = FileFormatReader(log_path=f"{path_log_data}/conversion-dns-train.log")

    for path in data:

        console.print(f"==> [bold yellow]{path}[/bold yellow]")

        path_new_file: str = fr"{path_dataset_new}\{path.split('\\')[-1].split('.')[0]}.json"

        result = reader.read(path)

        json_data = JsonData(path_new_file)

        json_data.write(result)


# Функция преобразования
def convertion(
        dns_key: str,
        path_log_data: str,
        path_file_json_dataset: str,
        path_dataset_new_dns: str,
    ):
    """
    :param dns_key:
    :param path_log_data:
    :param path_file_json_dataset:
    :param path_dataset_new_dns:
    """
    print()

    print(dns_key, "|",  path_dataset_new_dns, "|", path_file_json_dataset)

    json_data = JsonData(path_file_json_dataset)


    read_file_dataset(
        data=json_data.read()["dns"][dns_key.upper()],
        path_log_data=path_log_data,
        path_dataset_new=fr"{path_dataset_new_dns}\{dns_key.upper()}"
    )


