from rich.console import Console

from config import manage_commands, PATH_HOST_DATASETS_FILTER, PATH_TEMP_DATA, PATH_DNS_DATASETS_FILTER
from scripts.handlers.save_sort.save_sort_host_path_handler import HostSortedPathExportHandler
from scripts.handlers.save_sort.save_sort_dns_path_handler import DNSSortedPathExportHandler

console = Console()


def save_sort_host_dataset_handler():
    handler = HostSortedPathExportHandler(
        host_datasets_filter_path=PATH_HOST_DATASETS_FILTER,
        temp_data_path=PATH_TEMP_DATA,
    )

    result = handler.export_paths()
    console.print(
        "Host sorted path export completed.\n"
        f"JSON file: {result.json_file}\n"
        f"Scanned files: {result.scanned_files_count}\n"
        f"Counts by role/format: {result.counts_by_role_and_format}"
    )


def save_sort_dns_dataset_handler():
    handler = DNSSortedPathExportHandler(
        dns_datasets_filter_path=PATH_DNS_DATASETS_FILTER,
        temp_data_path=PATH_TEMP_DATA,
    )
    result = handler.export_paths()
    console.print(
        "DNS sorted path export completed.\n"
        f"JSON file: {result.json_file}\n"
        f"Scanned files: {result.scanned_files_count}\n"
        f"Counts by role/format: {result.counts_by_role_and_format}"
    )

def router_save(action: str):

    if action == "save-sort-host-dataset-handler":

        save_sort_host_dataset_handler()

    elif action == "save-sort-dns-dataset-handler":

        save_sort_dns_dataset_handler()

    else:
        print(manage_commands)