import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------- PATHS FOLDERS ---------------------- #

load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent

def _child_path(root: str, child: str) -> str:
    """Build a child path only when the parent path is configured."""
    root = root.strip()
    if not root:
        return ""
    return str(Path(root).expanduser() / child)


PATH_DATA_STORAGE: str = os.getenv("PATH_DATA_STORAGE", "")

PATH_REPORT: str = f'{PATH_DATA_STORAGE}/report'

PATH_FOLDER_DATASETS: str = os.getenv("PATH_FOLDER_DATASETS", "")

PATH_FOLDER_DATASETS_FILTER: str = os.getenv("PATH_FOLDER_DATASETS_FILTER", "")

PATH_TEMP_DATA: str = os.getenv(
    "PATH_TEMP_DATA",
    _child_path(PATH_DATA_STORAGE, "temp_data"),
)

PATH_HOST_DATASETS: str = os.getenv(
    "PATH_HOST_DATASETS",
    _child_path(PATH_FOLDER_DATASETS, "host"),
)

PATH_DNS_DATASETS: str = os.getenv(
    "PATH_DNS_DATASETS",
    _child_path(PATH_FOLDER_DATASETS, "dns"),
)

PATH_FILTER_LOG= f"{PATH_DATA_STORAGE}/logs/filter_log",

PATH_HOST_DATASETS_FILTER: str = os.getenv(
    "PATH_HOST_DATASETS_FILTER",
    _child_path(PATH_FOLDER_DATASETS_FILTER, "host"),
)
PATH_DNS_DATASETS_FILTER: str = os.getenv(
    "PATH_DNS_DATASETS_FILTER",
    _child_path(PATH_FOLDER_DATASETS_FILTER, "dns"),
)
