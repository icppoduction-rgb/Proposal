import os
import argparse

from pathlib import Path

from dotenv import load_dotenv

try:
    from rich.console import Console
except ModuleNotFoundError:
    class Console:  # type: ignore[override]
        """Fallback-консоль, если пакет rich не установлен."""

        @staticmethod
        def print(message: str) -> None:
            print(message)

from scripts.handlers.dns_dataset_handler import DNSDatasetHandler
from scripts.handlers.host_dataset_handler import HostDatasetHandler


load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent

# ---------------------- Variables for working with data sets ---------------------- #

PATH_FOLDER_DATASETS: str = os.getenv("PATH_FOLDER_DATASETS", "")

PATH_TEMP_DATA: str = os.getenv("PATH_TEMP_DATA", fr"{PROJECT_ROOT}\temp_data")

PATH_HOST_DATASETS: str = os.getenv(
    "PATH_HOST_DATASETS",
    fr"{PATH_FOLDER_DATASETS}\host" if PATH_FOLDER_DATASETS else "",
)

PATH_DNS_DATASETS: str = os.getenv(
    "PATH_DNS_DATASETS",
    fr"{PATH_FOLDER_DATASETS}\dns" if PATH_FOLDER_DATASETS else "",
)
# ------------------------------ Database settings ------------------------------ #

console = Console()

parser = argparse.ArgumentParser()

parser.add_argument("module", nargs="?")
parser.add_argument("service", nargs="?")
parser.add_argument("action", nargs="?")


# Функция управления
def manage() -> None:
    """
    Управляет запуском скриптов проекта через аргументы командной строки.
    """

    args, _unknown = parser.parse_known_args()

    match (args.module, args.service, args.action):
        # пример
        case ("handler", "example", "work_example"):
            pass

        case ("dataset", "dns", "analyze"):
            handler = DNSDatasetHandler(
                dns_datasets_path=PATH_DNS_DATASETS,
                temp_data_path=PATH_TEMP_DATA,
            )
            result = handler.analyze_and_save()
            console.print(
                "DNS dataset analysis completed.\n"
                f"Path JSON: {result.path_json_file}\n"
                f"Files JSON: {result.files_json_file}"
            )

        case ("host", "dataset", "analyze"):
            handler = HostDatasetHandler(
                host_datasets_path=PATH_HOST_DATASETS,
                temp_data_path=PATH_TEMP_DATA,
            )
            result = handler.analyze_and_save()
            console.print(
                "Host dataset analysis completed.\n"
                f"Path JSON: {result.path_json_file}\n"
                f"Files JSON: {result.files_json_file}"
            )

        case _:
            console.print(
                "Commands:\n"
                "python manage.py dataset dns analyze\n"
                "python manage.py host dataset analyze\n"
            )


if __name__ == "__main__":
    manage()
