import os
import argparse
import subprocess
from pathlib import Path

from dotenv import load_dotenv

try:
    from rich.console import Console
except ModuleNotFoundError:
    class Console:
        def print(self, *objects, **kwargs):
            print(*objects)

from scripts.database.duckdb_service import (
    DuckDBDockerConfig,
    DuckDBServiceError,
    build_duckdb_config,
    restart_duckdb,
    show_duckdb_logs,
    show_duckdb_status,
    start_duckdb,
    stop_duckdb,
)
from scripts.convertion.dns_convertion import convertion
from scripts.convertion.host_convertion import (
    HOST_SPLITS,
    HostConversionConfig,
    convert_host_datasets,
    print_host_conversion_summary,
)
from scripts.workdatasets.dataset_processing import build_processed_file_paths
from scripts.workdatasets.dataset_path import write_dataset_path, write_extensions
from scripts.workdatasets.dataset_processing import print_processing_result, process_datasets
from scripts.cleanup.dataset_format_cleanup import cleanup_unreadable_dataset_files, print_cleanup_result

load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent

# ---------------------- Variables for working with data sets ---------------------- #

PATH_DATASETS_FOLDER: str = os.getenv("PATH_DATASETS_FOLDER", "")
PATH_FILE_JSON_DATASET: str = os.getenv("PATH_FILE_JSON_DATASET", "")
PATH_FILE_JSON_EXTENSIONS: str = os.getenv("PATH_FILE_JSON_EXTENSIONS", "")
PATH_FILE_JSON_PROCESSED_DATASET, PATH_FILE_JSON_PROCESSED_EXTENSIONS = build_processed_file_paths(PATH_FILE_JSON_DATASET)

PATH_DATASETS_NEW_FOLDER: str = os.getenv("PATH_DATASETS_NEW_FOLDER", "")
PATH_DATASETS_NEW_DNS_FOLDER: str = os.getenv("PATH_DATASETS_NEW_DNS_FOLDER", "")
PATH_DATASETS_NEW_HOST_FOLDER: str = os.getenv(
    "PATH_DATASETS_NEW_HOST_FOLDER",
    os.path.join(PATH_DATASETS_NEW_FOLDER or "datasets-new", "host"),
)
PATH_DATASETS_HOST_FOLDER: str = os.path.join(PATH_DATASETS_FOLDER or "datasets", "host")
HOST_CONVERSION_WORKERS: int = int(os.getenv("HOST_CONVERSION_WORKERS", str(max(1, min(os.cpu_count() or 1, 4)))))

PATH_LOG_DATA: str = os.getenv("PATH_LOG_DATA", "")

# ------------------------------ Database settings ------------------------------ #

DUCKDB_DATA_PATH: str = os.getenv("DUCKDB_DATA_PATH", "")
DUCKDB_DATABASE: str = os.getenv("DUCKDB_DATABASE", "")

console = Console()

parser = argparse.ArgumentParser()

parser.add_argument("module", nargs="?")
parser.add_argument("service", nargs="?")
parser.add_argument("action", nargs="?")


def build_project_duckdb_config() -> DuckDBDockerConfig:
    return build_duckdb_config(
        project_root=PROJECT_ROOT,
        data_path_value=DUCKDB_DATA_PATH,
        database=DUCKDB_DATABASE,
    )


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

        case ("json", "process", "datasets-dry-run"):
            result = process_datasets(
                datasets_root=PATH_DATASETS_FOLDER,
                source_path_file=PATH_FILE_JSON_DATASET,
                dry_run=True,
            )
            print_processing_result(result, dry_run=True)

        case ("json", "process", "datasets"):
            result = process_datasets(
                datasets_root=PATH_DATASETS_FOLDER,
                source_path_file=PATH_FILE_JSON_DATASET,
                dry_run=False,
            )
            print_processing_result(result, dry_run=False)

        case ("json", "cleanup", "unreadable-dry-run"):
            result = cleanup_unreadable_dataset_files(
                datasets_root=PATH_DATASETS_FOLDER,
                processed_path_file=PATH_FILE_JSON_PROCESSED_DATASET,
                processed_extensions_file=PATH_FILE_JSON_PROCESSED_EXTENSIONS,
                dry_run=True,
            )
            print_cleanup_result(result, dry_run=True)

        case ("json", "cleanup", "unreadable"):
            result = cleanup_unreadable_dataset_files(
                datasets_root=PATH_DATASETS_FOLDER,
                processed_path_file=PATH_FILE_JSON_PROCESSED_DATASET,
                processed_extensions_file=PATH_FILE_JSON_PROCESSED_EXTENSIONS,
                dry_run=False,
            )
            print_cleanup_result(result, dry_run=False)

        case ("convert", "dns", "train"):

            console.print("==> [bold blue]start command: convert dns train[/bold blue]")
            convertion(
                dns_key=args.action,
                path_log_data=PATH_LOG_DATA,
                path_file_json_dataset=PATH_FILE_JSON_DATASET,
                path_dataset_new_dns=PATH_DATASETS_NEW_DNS_FOLDER
            )

        case ("convert", "dns", "validation"):

            console.print("==> [bold blue]start command: convert dns validation[/bold blue]")
            convertion(
                dns_key=args.action,
                path_log_data=PATH_LOG_DATA,
                path_file_json_dataset=PATH_FILE_JSON_DATASET,
                path_dataset_new_dns=PATH_DATASETS_NEW_DNS_FOLDER
            )

        case ("convert", "dns", "test"):

            console.print("==> [bold blue]start command: convert dns test[/bold blue]")
            convertion(
                dns_key=args.action,
                path_log_data=PATH_LOG_DATA,
                path_file_json_dataset=PATH_FILE_JSON_DATASET,
                path_dataset_new_dns=PATH_DATASETS_NEW_DNS_FOLDER
            )

        case ("convert", "host", "all"):

            console.print("==> [bold blue]start command: convert host all[/bold blue]")
            summary = convert_host_datasets(
                HostConversionConfig(
                    source_root=PATH_DATASETS_HOST_FOLDER,
                    target_root=PATH_DATASETS_NEW_HOST_FOLDER,
                    splits=HOST_SPLITS,
                    workers=HOST_CONVERSION_WORKERS,
                )
            )
            print_host_conversion_summary(summary)

        case ("convert", "host", "train" | "validation" | "experiments" | "test"):

            split = args.action.upper()
            console.print(f"==> [bold blue]start command: convert host {args.action}[/bold blue]")
            summary = convert_host_datasets(
                HostConversionConfig(
                    source_root=PATH_DATASETS_HOST_FOLDER,
                    target_root=PATH_DATASETS_NEW_HOST_FOLDER,
                    splits=(split,),
                    workers=HOST_CONVERSION_WORKERS,
                )
            )
            print_host_conversion_summary(summary)

        case ("database" | "db", "duckdb", "start"):
            console.print("==> [bold blue]start command: database duckdb start[/bold blue]")
            start_duckdb(build_project_duckdb_config())

        case ("database" | "db", "duckdb", "stop"):
            console.print("==> [bold blue]start command: database duckdb stop[/bold blue]")
            stop_duckdb(build_project_duckdb_config())

        case ("database" | "db", "duckdb", "restart"):
            console.print("==> [bold blue]start command: database duckdb restart[/bold blue]")
            restart_duckdb(build_project_duckdb_config())

        case ("database" | "db", "duckdb", "status"):
            console.print("==> [bold blue]start command: database duckdb status[/bold blue]")
            show_duckdb_status(build_project_duckdb_config())

        case ("database" | "db", "duckdb", "logs"):
            console.print("==> [bold blue]start command: database duckdb logs[/bold blue]")
            show_duckdb_logs(build_project_duckdb_config())

        case _:
            print(
                "Commands:\n"
                "json write path-dataset: Write path file dataset in json format\n"
                "json write extensions: Write file extensions in json format\n"
                "json process datasets-dry-run: Show selected datasets and directories to delete\n"
                "json process datasets: Write processed dataset json files and delete unselected datasets\n"
                "json cleanup unreadable-dry-run: Show unreadable files selected for deletion\n"
                "json cleanup unreadable: Delete unreadable files and update processed json files\n"
                "convert dns train: \n"
                "convert host all: Convert all host dataset splits to datasets-new/host\n"
                "convert host train|validation|experiments|test: Convert one host split to datasets-new/host\n"
                "database duckdb start: Start DuckDB container via Docker Compose\n"
                "database duckdb stop: Stop DuckDB container and remove Compose resources\n"
                "database duckdb restart: Restart DuckDB container via Docker Compose\n"
                "database duckdb status: Show DuckDB Compose service status\n"
                "database duckdb logs: Show last 100 DuckDB service logs\n"
            )


if __name__ == "__main__":
    try:
        manage()
    except DuckDBServiceError as exc:
        console.print(f"[bold red]DuckDB configuration error:[/bold red] {exc}")
        raise SystemExit(2) from exc
    except subprocess.CalledProcessError as exc:
        console.print(f"[bold red]Command failed with exit code {exc.returncode}:[/bold red] {' '.join(exc.cmd)}")
        raise SystemExit(exc.returncode) from exc
