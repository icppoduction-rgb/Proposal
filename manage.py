import os
import argparse

from dotenv import load_dotenv

from scripts.dataset_path import write_dataset_path, write_extensions

load_dotenv()

# ---------------------- Variables for working with data sets ---------------------- #

PATH_DATASETS_FOLDER: str = os.getenv("PATH_DATASETS_FOLDER", "")
PATH_FILE_JSON_DATASET: str = os.getenv("PATH_FILE_JSON_DATASET", "")
PATH_FILE_JSON_EXTENSIONS: str = os.getenv("PATH_FILE_JSON_EXTENSIONS", "")


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

    args = parser.parse_args()

    match (args.module, args.service, args.action):

        case ("json", "write", "path-dataset"):

            write_dataset_path(path_folder=PATH_DATASETS_FOLDER, path_file=PATH_FILE_JSON_DATASET)

        case ("json", "write", "extensions"):
            write_extensions(path_folder=PATH_DATASETS_FOLDER, path_file=PATH_FILE_JSON_EXTENSIONS)
        case _:
            print(
                "Commands:\n"
                "json write path-dataset: Write path file dataset in json format\n"
            )


if __name__ == "__main__":
    manage()