from rich.console import Console

from config import manage_commands, PATH_TEMP_DATA, PATH_FILTER_LOG
from scripts.handlers.filter_dataset.filter_host_dataset_handler import HostDatasetFilterHandler

console = Console()

def filter_host_dataset_handler():
    handler = HostDatasetFilterHandler(
        temp_data_path=PATH_TEMP_DATA,
        log_file_path=PATH_FILTER_LOG,
    )
    result = handler.filter_and_save()
    console.print(
        "Host dataset filter_dataset completed.\n"
        f"Path JSON: {result.path_json_file}\n"
        f"Files JSON: {result.files_json_file}\n"
        f"Log file: {result.log_file}\n"
        f"Kept files: {result.kept_files_count}\n"
        f"Excluded files: {result.excluded_files_count}\n"
        f"Excluded reasons: {result.excluded_by_reason}"
    )

def router_filter(action: str):

    if action == "filter-host-dataset-handler":

        filter_host_dataset_handler()

    else:
        print(manage_commands)