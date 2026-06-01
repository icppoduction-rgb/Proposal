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
from scripts.handlers.filter_host_dataset_handler import HostDatasetFilterHandler
from scripts.handlers.sort_host_dataset_handler import HostDatasetSortHandler
from scripts.handlers.save_sort_host_path_handler import HostSortedPathExportHandler
from scripts.handlers.sort_dns_dataset_handler import DNSDatasetSortHandler
from scripts.handlers.save_sort_dns_path_handler import DNSSortedPathExportHandler
from scripts.handlers.analyze_host_csv_dataset_handler import HostCSVContentAnalysisHandler
from scripts.handlers.analyze_host_auth_log_dataset_handler import HostAuthLogContentAnalysisHandler
from scripts.handlers.analyze_host_cpu_log_dataset_handler import HostCPULogContentAnalysisHandler
from scripts.handlers.analyze_host_diskio_log_dataset_handler import HostDiskioLogContentAnalysisHandler
from scripts.handlers.analyze_host_filesystem_log_dataset_handler import (
    HostFilesystemLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_fsstat_log_dataset_handler import (
    HostFSStatLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_ghc_dataset_handler import (
    HostGHCContentAnalysisHandler,
)
from scripts.handlers.analyze_host_info_dataset_handler import (
    HostInfoContentAnalysisHandler,
)
from scripts.handlers.analyze_host_journal_dataset_handler import (
    HostJournalContentAnalysisHandler,
)
from scripts.handlers.analyze_host_journal_tilde_dataset_handler import (
    HostJournalTildeContentAnalysisHandler,
)
from scripts.handlers.analyze_host_json_dataset_handler import (
    HostJSONContentAnalysisHandler,
)
from scripts.handlers.analyze_host_json_1_dataset_handler import (
    HostJSON1ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_load_log_dataset_handler import (
    HostLoadLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_log_dataset_handler import (
    HostLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_log_1_dataset_handler import (
    HostLog1ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_log_2_dataset_handler import (
    HostLog2ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_log_3_dataset_handler import (
    HostLog3ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_mail_info_1_dataset_handler import (
    HostMailInfo1ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_mail_warn_1_dataset_handler import (
    HostMailWarn1ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_mainlog_dataset_handler import (
    HostMainlogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_mainlog_1_dataset_handler import (
    HostMainlog1ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_mainlog_2_dataset_handler import (
    HostMainlog2ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_mainlog_3_dataset_handler import (
    HostMainlog3ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_memory_log_dataset_handler import (
    HostMemoryLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_messages_dataset_handler import (
    HostMessagesContentAnalysisHandler,
)
from scripts.handlers.analyze_host_messages_1_dataset_handler import (
    HostMessages1ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_netflow_ids_dataset_handler import (
    HostNetflowIdsContentAnalysisHandler,
)
from scripts.handlers.analyze_host_network_log_dataset_handler import (
    HostNetworkLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_pcap_dataset_handler import (
    HostPCAPContentAnalysisHandler,
)
from scripts.handlers.analyze_host_process_log_dataset_handler import (
    HostProcessLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_process_summary_log_dataset_handler import (
    HostProcessSummaryLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_sc_dataset_handler import (
    HostSCContentAnalysisHandler,
)
from scripts.handlers.analyze_host_service_log_dataset_handler import (
    HostServiceLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_socket_summary_log_dataset_handler import (
    HostSocketSummaryLogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_syslog_dataset_handler import (
    HostSyslogContentAnalysisHandler,
)
from scripts.handlers.analyze_host_syslog_1_dataset_handler import (
    HostSyslog1ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_syslog_2_dataset_handler import (
    HostSyslog2ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_syslog_3_dataset_handler import (
    HostSyslog3ContentAnalysisHandler,
)
from scripts.handlers.analyze_host_syslog_4_dataset_handler import (
    HostSyslog4ContentAnalysisHandler,
)


load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent

# ---------------------- Variables for working with data sets ---------------------- #

PATH_FOLDER_DATASETS: str = os.getenv("PATH_FOLDER_DATASETS", "")

PATH_FOLDER_DATASETS_FILTER: str = os.getenv('PATH_FOLDER_DATASETS_FILTER', "")

PATH_TEMP_DATA: str = os.getenv("PATH_TEMP_DATA", fr"{PROJECT_ROOT}\temp_data")

PATH_HOST_DATASETS: str = os.getenv(
    "PATH_HOST_DATASETS",
    fr"{PATH_FOLDER_DATASETS}\host" if PATH_FOLDER_DATASETS else "",
)

PATH_DNS_DATASETS: str = os.getenv(
    "PATH_DNS_DATASETS",
    fr"{PATH_FOLDER_DATASETS}\dns" if PATH_FOLDER_DATASETS else "",
)

PATH_FILTER_LOG: str = os.getenv(
    "PATH_FILTER_LOG",
    str(PROJECT_ROOT / "logs" / "filter.log"),
)

PATH_HOST_DATASETS_FILTER: str = fr'{PATH_FOLDER_DATASETS_FILTER}\host'
PATH_DNS_DATASETS_FILTER: str = fr'{PATH_FOLDER_DATASETS_FILTER}\dns'

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

        case ("host", "dataset", "filter"):
            handler = HostDatasetFilterHandler(
                temp_data_path=PATH_TEMP_DATA,
                log_file_path=PATH_FILTER_LOG,
            )
            result = handler.filter_and_save()
            console.print(
                "Host dataset filter completed.\n"
                f"Path JSON: {result.path_json_file}\n"
                f"Files JSON: {result.files_json_file}\n"
                f"Log file: {result.log_file}\n"
                f"Kept files: {result.kept_files_count}\n"
                f"Excluded files: {result.excluded_files_count}\n"
                f"Excluded reasons: {result.excluded_by_reason}"
            )

        case ("host", "dataset", "sort"):
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

        case ("host", "dataset", "save-paths"):
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

        case ("host", "dataset", "analyze-csv-content"):
            handler = HostCSVContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host CSV content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-auth-log-content"):
            handler = HostAuthLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host auth.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-cpu-log-content"):
            handler = HostCPULogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host cpu.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-diskio-log-content"):
            handler = HostDiskioLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host diskio.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-filesystem-log-content"):
            handler = HostFilesystemLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host filesystem.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-fsstat-log-content"):
            handler = HostFSStatLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host fsstat.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-ghc-content"):
            handler = HostGHCContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host ghc content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-info-content"):
            handler = HostInfoContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host info content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-journal-content"):
            handler = HostJournalContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host journal content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-journal-tilde-content"):
            handler = HostJournalTildeContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host journal~ content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-json-content"):
            handler = HostJSONContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host json content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-json-1-content"):
            handler = HostJSON1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host json-1 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-load-log-content"):
            handler = HostLoadLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host load.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-log-content"):
            handler = HostLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-log-1-content"):
            handler = HostLog1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host log-1 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-log-2-content"):
            handler = HostLog2ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host log-2 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-log-3-content"):
            handler = HostLog3ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host log-3 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-mail-info-1-content"):
            handler = HostMailInfo1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host mail-info-1 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-mail-warn-1-content"):
            handler = HostMailWarn1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host mail-warn-1 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-mainlog-content"):
            handler = HostMainlogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host mainlog content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-mainlog-1-content"):
            handler = HostMainlog1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host mainlog-1 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-mainlog-2-content"):
            handler = HostMainlog2ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host mainlog-2 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-mainlog-3-content"):
            handler = HostMainlog3ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host mainlog-3 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-memory-log-content"):
            handler = HostMemoryLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host memory.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-messages-content"):
            handler = HostMessagesContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host messages content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-messages-1-content"):
            handler = HostMessages1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host messages-1 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-netflow-ids-content"):
            handler = HostNetflowIdsContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host netflow_ids content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-network-log-content"):
            handler = HostNetworkLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host network.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-pcap-content"):
            handler = HostPCAPContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host pcap content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-process-log-content"):
            handler = HostProcessLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host process.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-process-summary-log-content"):
            handler = HostProcessSummaryLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host process.summary.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-sc-content"):
            handler = HostSCContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host sc content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-service-log-content"):
            handler = HostServiceLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host service.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-socket-summary-log-content"):
            handler = HostSocketSummaryLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host socket.summary.log content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-syslog-content"):
            handler = HostSyslogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host syslog content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-syslog-1-content"):
            handler = HostSyslog1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host syslog-1 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-syslog-2-content"):
            handler = HostSyslog2ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host syslog-2 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-syslog-3-content"):
            handler = HostSyslog3ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host syslog-3 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("host", "dataset", "analyze-syslog-4-content"):
            handler = HostSyslog4ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host syslog-4 content analysis completed.\n"
                f"Summary JSON: {result.summary_json_file}\n"
                f"RU doc: {result.docs_ru_file}\n"
                f"EN doc: {result.docs_en_file}\n"
                f"RU index: {result.docs_ru_readme_file}\n"
                f"EN index: {result.docs_en_readme_file}\n"
                f"RU report: {result.report_ru_file}\n"
                f"EN report: {result.report_en_file}\n"
                f"Total files: {result.total_files_count}\n"
                f"Sampled files: {result.sampled_files_count}\n"
                f"Status: {result.status}"
            )

        case ("dns", "dataset", "sort") | ("dataset", "dns", "sort"):
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

        case ("dns", "dataset", "save-paths") | ("dataset", "dns", "save-paths"):
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

        case _:
            console.print(
                "Commands:\n"
                "python manage.py dataset dns analyze\n"
                "python manage.py dataset dns sort\n"
                "python manage.py dns dataset sort\n"
                "python manage.py dataset dns save-paths\n"
                "python manage.py dns dataset save-paths\n"
                "python manage.py host dataset analyze\n"
                "python manage.py host dataset filter\n"
                "python manage.py host dataset sort\n"
                "python manage.py host dataset save-paths\n"
                "python manage.py host dataset analyze-csv-content\n"
                "python manage.py host dataset analyze-auth-log-content\n"
                "python manage.py host dataset analyze-cpu-log-content\n"
                "python manage.py host dataset analyze-diskio-log-content\n"
                "python manage.py host dataset analyze-filesystem-log-content\n"
                "python manage.py host dataset analyze-fsstat-log-content\n"
                "python manage.py host dataset analyze-ghc-content\n"
                "python manage.py host dataset analyze-info-content\n"
                "python manage.py host dataset analyze-journal-content\n"
                "python manage.py host dataset analyze-journal-tilde-content\n"
                "python manage.py host dataset analyze-json-content\n"
                "python manage.py host dataset analyze-json-1-content\n"
                "python manage.py host dataset analyze-load-log-content\n"
                "python manage.py host dataset analyze-log-content\n"
                "python manage.py host dataset analyze-log-1-content\n"
                "python manage.py host dataset analyze-log-2-content\n"
                "python manage.py host dataset analyze-log-3-content\n"
                "python manage.py host dataset analyze-mail-info-1-content\n"
                "python manage.py host dataset analyze-mail-warn-1-content\n"
                "python manage.py host dataset analyze-mainlog-content\n"
                "python manage.py host dataset analyze-mainlog-1-content\n"
                "python manage.py host dataset analyze-mainlog-2-content\n"
                "python manage.py host dataset analyze-mainlog-3-content\n"
                "python manage.py host dataset analyze-memory-log-content\n"
                "python manage.py host dataset analyze-messages-content\n"
                "python manage.py host dataset analyze-messages-1-content\n"
                "python manage.py host dataset analyze-netflow-ids-content\n"
                "python manage.py host dataset analyze-network-log-content\n"
                "python manage.py host dataset analyze-pcap-content\n"
                "python manage.py host dataset analyze-process-log-content\n"
                "python manage.py host dataset analyze-process-summary-log-content\n"
                "python manage.py host dataset analyze-sc-content\n"
                "python manage.py host dataset analyze-service-log-content\n"
                "python manage.py host dataset analyze-socket-summary-log-content\n"
                "python manage.py host dataset analyze-syslog-content\n"
                "python manage.py host dataset analyze-syslog-1-content\n"
                "python manage.py host dataset analyze-syslog-2-content\n"
                "python manage.py host dataset analyze-syslog-3-content\n"
                "python manage.py host dataset analyze-syslog-4-content\n"
            )


if __name__ == "__main__":
    manage()
