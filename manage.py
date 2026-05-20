import os
import argparse

from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent

# ---------------------- Variables for working with data sets ---------------------- #

PATH_DATASETS_FOLDER: str = os.getenv("PATH_DATASETS_FOLDER", "")
PATH_FILE_JSON_DATASET: str = os.getenv("PATH_FILE_JSON_DATASET", "")
PATH_FILE_JSON_EXTENSIONS: str = os.getenv("PATH_FILE_JSON_EXTENSIONS", "")

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

        case _:
            console.print(
                "Commands:\n"
            )


if __name__ == "__main__":
    manage()