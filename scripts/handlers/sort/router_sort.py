from rich.console import Console

from scripts.handlers.sort.sort_host_dataset_handler import HostDatasetSortHandler
from scripts.handlers.sort.sort_dns_dataset_handler import DNSDatasetSortHandler
from config import manage_commands, PATH_DNS_DATASETS_FILTER, PATH_TEMP_DATA, PATH_HOST_DATASETS_FILTER

console = Console()


def sort_host_dataset_handler():
    handler = HostDatasetSortHandler(
        temp_data_path=PATH_TEMP_DATA,
        host_datasets_filter_path=PATH_HOST_DATASETS_FILTER,
    )
    result = handler.sort_and_prepare()
    console.print(
        "Host dataset sort completed.\n"
        f"Sorted root: {result.sorted_root_path}\n"
        f"Summary JSON: {result.summary_json_file}\n"
        f"Created hardlinks: {result.created_links_count}\n"
        f"Copied files: {result.copied_files_count}\n"
        f"Skipped existing: {result.skipped_existing_count}\n"
        f"Missing source files: {result.missing_source_count}\n"
        f"Name mismatches: {result.name_mismatch_count}\n"
        f"Formats by role: {result.files_by_role_and_format}"
    )


def sort_dns_dataset_handler():
    handler = DNSDatasetSortHandler(
        temp_data_path=PATH_TEMP_DATA,
        dns_datasets_filter_path=PATH_DNS_DATASETS_FILTER,
    )
    result = handler.sort_and_prepare()

    console.print(
        "DNS dataset sort completed.\n"
        f"Sorted root: {result.sorted_root_path}\n"
        f"Summary JSON: {result.summary_json_file}\n"
        f"Created hardlinks: {result.created_links_count}\n"
        f"Copied files: {result.copied_files_count}\n"
        f"Skipped existing: {result.skipped_existing_count}\n"
        f"Missing source files: {result.missing_source_count}\n"
        f"Name mismatches: {result.name_mismatch_count}\n"
        f"Formats by role: {result.files_by_role_and_format}"
    )

def router_sort(action :str):


    if action == "sort-host-dataset-handler":

       sort_host_dataset_handler()

    elif action == "sort-dns-dataset-handler":

        sort_dns_dataset_handler()

    else:
        print(manage_commands)
