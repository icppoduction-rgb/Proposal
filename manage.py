import os
import argparse

from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console


load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent

# ---------------------- Variables for working with data sets ---------------------- #

PATH_FOLDER_DATASETS: str =  os.getenv("PATH_FOLDER_DATASETS", "")

PATH_TEMP_DATA: str = fr"{PROJECT_ROOT}\temp_data"

PATH_DNS_DATASETS: str = fr"{PATH_FOLDER_DATASETS}\dns"
# ------------------------------ Database settings ------------------------------ #

console = Console()

parser = argparse.ArgumentParser()

parser.add_argument("module", nargs="?")
parser.add_argument("service", nargs="?")
parser.add_argument("action", nargs="?")

# Функция управления
def manage():
    """
    This feature manages the project using command line commands that are used to
    run scripts and to start and stop the project.
    """

    args, _unknown = parser.parse_known_args()

    match (args.module, args.service, args.action):

        case ("handlers", "file-processing", "collection-file-dns"):

            pass

        case _:
            console.print(
                "Commands:\n"
            )


if __name__ == "__main__":
    manage()