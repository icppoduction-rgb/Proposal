from rich.console import Console

from config import manage_commands, PATH_DNS_DATASETS, PATH_TEMP_DATA, PATH_HOST_DATASETS
from scripts.handlers.analyze_dataset.dns_dataset_handler import DNSDatasetHandler
from scripts.handlers.analyze_dataset.host_dataset_handler import HostDatasetHandler

console = Console()

def dns_dataset_handler():

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

def host_dataset_handler():
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


def router_analyze(action: str):

   if action == "dns-dataset-handler":
       dns_dataset_handler()

   elif action == "host-dataset-handler":
       host_dataset_handler()

   else:
       print(manage_commands)