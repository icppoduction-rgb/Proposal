# -*- coding: cp1251 -*-

import argparse

from config import *

try:
    from rich.console import Console
except ModuleNotFoundError:
    class Console:  # type: ignore[override]
        """Fallback-консоль, если пакет rich не установлен."""

        @staticmethod
        def print(message: str) -> None:
            print(message)

from scripts.handlers.host_analyze.analyze_host_diskio_log_dataset_handler import HostDiskioLogContentAnalysisHandler
from scripts.handlers.host_analyze.analyze_host_filesystem_log_dataset_handler import (
    HostFilesystemLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_fsstat_log_dataset_handler import (
    HostFSStatLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_ghc_dataset_handler import (
    HostGHCContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_info_dataset_handler import (
    HostInfoContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_journal_dataset_handler import (
    HostJournalContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_journal_tilde_dataset_handler import (
    HostJournalTildeContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_json_dataset_handler import (
    HostJSONContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_json_1_dataset_handler import (
    HostJSON1ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_load_log_dataset_handler import (
    HostLoadLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_log_dataset_handler import (
    HostLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_log_1_dataset_handler import (
    HostLog1ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_log_2_dataset_handler import (
    HostLog2ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_log_3_dataset_handler import (
    HostLog3ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_mail_info_1_dataset_handler import (
    HostMailInfo1ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_mail_warn_1_dataset_handler import (
    HostMailWarn1ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_mainlog_dataset_handler import (
    HostMainlogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_mainlog_1_dataset_handler import (
    HostMainlog1ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_mainlog_2_dataset_handler import (
    HostMainlog2ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_mainlog_3_dataset_handler import (
    HostMainlog3ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_memory_log_dataset_handler import (
    HostMemoryLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_messages_dataset_handler import (
    HostMessagesContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_messages_1_dataset_handler import (
    HostMessages1ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_netflow_ids_dataset_handler import (
    HostNetflowIdsContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_network_log_dataset_handler import (
    HostNetworkLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_pcap_dataset_handler import (
    HostPCAPContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_process_log_dataset_handler import (
    HostProcessLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_process_summary_log_dataset_handler import (
    HostProcessSummaryLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_sc_dataset_handler import (
    HostSCContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_service_log_dataset_handler import (
    HostServiceLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_socket_summary_log_dataset_handler import (
    HostSocketSummaryLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_syslog_dataset_handler import (
    HostSyslogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_syslog_1_dataset_handler import (
    HostSyslog1ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_syslog_2_dataset_handler import (
    HostSyslog2ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_syslog_3_dataset_handler import (
    HostSyslog3ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_syslog_4_dataset_handler import (
    HostSyslog4ContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_syslog_log_dataset_handler import (
    HostSyslogLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_txt_dataset_handler import (
    HostTXTContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_test_bson_dataset_handler import (
    HostTestBSONContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_test_csv_dataset_handler import (
    HostTestCSVContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_test_json_dataset_handler import (
    HostTestJSONContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_test_log_dataset_handler import (
    HostTestLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_test_netflow_day_dataset_handler import (
    HostTestNetflowDayContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_test_txt_dataset_handler import (
    HostTestTXTContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_test_wls_day_dataset_handler import (
    HostTestWLSDayContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_validation_cap_dataset_handler import (
    HostValidationCAPContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_validation_csv_dataset_handler import (
    HostValidationCSVContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_validation_json_dataset_handler import (
    HostValidationJSONContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_validation_netflow_day_dataset_handler import (
    HostValidationNetflowDayContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_validation_pcap_dataset_handler import (
    HostValidationPCAPContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_validation_pcapng_dataset_handler import (
    HostValidationPCAPNGContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_validation_txt_dataset_handler import (
    HostValidationTXTContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_validation_wls_day_dataset_handler import (
    HostValidationWLSDayContentAnalysisHandler,
)
from scripts.handlers.dns_analyze.analyze_dns_train_csv_dataset_handler import (
    DNSTrainCSVContentAnalysisHandler,
)
from scripts.handlers.dns_analyze.analyze_dns_train_pcap_dataset_handler import (
    DNSTrainPCAPContentAnalysisHandler,
)
from scripts.handlers.dns_analyze.analyze_dns_train_pcap_csv_dataset_handler import (
    DNSTrainPCAPCSVContentAnalysisHandler,
)
from scripts.handlers.dns_analyze.analyze_dns_test_csv_dataset_handler import (
    DNSTestCSVContentAnalysisHandler,
)
from scripts.handlers.dns_analyze.analyze_dns_test_pcap_dataset_handler import (
    DNSTestPCAPContentAnalysisHandler,
)
from scripts.handlers.dns_analyze.analyze_dns_test_pcap_csv_dataset_handler import (
    DNSTestPCAPCSVContentAnalysisHandler,
)
from scripts.handlers.dns_analyze.analyze_dns_validation_pcap_dataset_handler import (
    DNSValidationPCAPContentAnalysisHandler,
)
from scripts.handlers.dns_analyze.analyze_dns_validation_txt_dataset_handler import (
    DNSValidationTXTContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_uptime_log_dataset_handler import (
    HostUptimeLogContentAnalysisHandler,
)
from scripts.handlers.host_analyze.analyze_host_xml_dataset_handler import (
    HostXMLContentAnalysisHandler,
)


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

    from scripts.router_script import router_commands

    args, _unknown = parser.parse_known_args()

    router_commands(args.module, args.service, args.action)

    match (args.module, args.service, args.action):

        case ("handlers", "host-analyze", "analyze-diskio-log-content"):
            handler = HostDiskioLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-filesystem-log-content"):
            handler = HostFilesystemLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-fsstat-log-content"):
            handler = HostFSStatLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-ghc-content"):
            handler = HostGHCContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-info-content"):
            handler = HostInfoContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-journal-content"):
            handler = HostJournalContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-journal-tilde-content"):
            handler = HostJournalTildeContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-json-content"):
            handler = HostJSONContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-json-1-content"):
            handler = HostJSON1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-load-log-content"):
            handler = HostLoadLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-log-content"):
            handler = HostLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-log-1-content"):
            handler = HostLog1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-log-2-content"):
            handler = HostLog2ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-log-3-content"):
            handler = HostLog3ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-mail-info-1-content"):
            handler = HostMailInfo1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-mail-warn-1-content"):
            handler = HostMailWarn1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-mainlog-content"):
            handler = HostMainlogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-mainlog-1-content"):
            handler = HostMainlog1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-mainlog-2-content"):
            handler = HostMainlog2ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-mainlog-3-content"):
            handler = HostMainlog3ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-memory-log-content"):
            handler = HostMemoryLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-messages-content"):
            handler = HostMessagesContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-messages-1-content"):
            handler = HostMessages1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-netflow-ids-content"):
            handler = HostNetflowIdsContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-network-log-content"):
            handler = HostNetworkLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-pcap-content"):
            handler = HostPCAPContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-process-log-content"):
            handler = HostProcessLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-process-summary-log-content"):
            handler = HostProcessSummaryLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-sc-content"):
            handler = HostSCContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-service-log-content"):
            handler = HostServiceLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-socket-summary-log-content"):
            handler = HostSocketSummaryLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-syslog-content"):
            handler = HostSyslogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-syslog-1-content"):
            handler = HostSyslog1ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-syslog-2-content"):
            handler = HostSyslog2ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-syslog-3-content"):
            handler = HostSyslog3ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-syslog-4-content"):
            handler = HostSyslog4ContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
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

        case ("handlers", "host-analyze", "analyze-syslog-log-content"):
            handler = HostSyslogLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host syslog.log content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-txt-content"):
            handler = HostTXTContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host txt content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-test-bson-content"):
            handler = HostTestBSONContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host TEST bson content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-test-csv-content"):
            handler = HostTestCSVContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host TEST csv content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-test-json-content"):
            handler = HostTestJSONContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host TEST json content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-test-log-content"):
            handler = HostTestLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host TEST log content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-test-netflow-day-content"):
            handler = HostTestNetflowDayContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host TEST netflow_day content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-test-txt-content"):
            handler = HostTestTXTContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host TEST txt content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-test-wls-day-content"):
            handler = HostTestWLSDayContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host TEST wls_day content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-validation-cap-content"):
            handler = HostValidationCAPContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host VALIDATION cap content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-validation-csv-content"):
            handler = HostValidationCSVContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host VALIDATION csv content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-validation-json-content"):
            handler = HostValidationJSONContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host VALIDATION json content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-validation-netflow-day-content"):
            handler = HostValidationNetflowDayContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host VALIDATION netflow_day content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-validation-pcap-content"):
            handler = HostValidationPCAPContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host VALIDATION pcap content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-validation-pcapng-content"):
            handler = HostValidationPCAPNGContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host VALIDATION pcapng content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-validation-txt-content"):
            handler = HostValidationTXTContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host VALIDATION txt content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-validation-wls-day-content"):
            handler = HostValidationWLSDayContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host VALIDATION wls_day content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-uptime-log-content"):
            handler = HostUptimeLogContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host uptime.log content analysis completed.\n"
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

        case ("handlers", "host-analyze", "analyze-xml-content"):
            handler = HostXMLContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "Host xml content analysis completed.\n"
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

        case ("handlers", "dns-analyze", "analyze-train-csv-content"):
            handler = DNSTrainCSVContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "DNS TRAIN csv content analysis completed.\n"
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

        case ("handlers", "dns-analyze", "analyze-train-pcap-content"):
            handler = DNSTrainPCAPContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "DNS TRAIN pcap content analysis completed.\n"
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

        case ("handlers", "dns-analyze", "analyze-train-pcap-csv-content"):
            handler = DNSTrainPCAPCSVContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "DNS TRAIN pcap.csv content analysis completed.\n"
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

        case ("handlers", "dns-analyze", "analyze-test-csv-content"):
            handler = DNSTestCSVContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "DNS TEST csv content analysis completed.\n"
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

        case ("handlers", "dns-analyze", "analyze-test-pcap-content"):
            handler = DNSTestPCAPContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "DNS TEST pcap content analysis completed.\n"
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

        case ("handlers", "dns-analyze", "analyze-test-pcap-csv-content"):
            handler = DNSTestPCAPCSVContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "DNS TEST pcap.csv content analysis completed.\n"
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

        case ("handlers", "dns-analyze", "analyze-validation-pcap-content"):
            handler = DNSValidationPCAPContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "DNS VALIDATION pcap content analysis completed.\n"
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

        case ("handlers", "dns-analyze", "analyze-validation-txt-content"):
            handler = DNSValidationTXTContentAnalysisHandler(
                temp_data_path=PATH_TEMP_DATA,
                project_root=PROJECT_ROOT,
                report_path=PATH_REPORT,
            )
            result = handler.analyze_and_generate_docs()
            console.print(
                "DNS VALIDATION txt content analysis completed.\n"
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

        case _:
            console.print(manage_commands)


if __name__ == "__main__":
    manage()
