from scripts.handlers.host_analyze import (
    HostCSVContentAnalysisHandler,
    HostAuthLogContentAnalysisHandler,
    HostCPULogContentAnalysisHandler,
    HostDiskioLogContentAnalysisHandler,
    HostFilesystemLogContentAnalysisHandler,
    HostFSStatLogContentAnalysisHandler,
    HostGHCContentAnalysisHandler,
    HostInfoContentAnalysisHandler,
    HostJournalContentAnalysisHandler,
    HostJournalTildeContentAnalysisHandler,
    HostJSONContentAnalysisHandler,
    HostJSON1ContentAnalysisHandler,
    HostLoadLogContentAnalysisHandler,
    HostLogContentAnalysisHandler,
    HostLog1ContentAnalysisHandler,
    HostLog2ContentAnalysisHandler,
    HostLog3ContentAnalysisHandler,
    HostMailInfo1ContentAnalysisHandler,
    HostMailWarn1ContentAnalysisHandler,
    HostMainlogContentAnalysisHandler,
    HostMainlog1ContentAnalysisHandler,
    HostMainlog2ContentAnalysisHandler,
    HostMainlog3ContentAnalysisHandler,
    HostMemoryLogContentAnalysisHandler,
    HostMessagesContentAnalysisHandler,
    HostMessages1ContentAnalysisHandler,
    HostNetflowIdsContentAnalysisHandler,
    HostNetworkLogContentAnalysisHandler,
    HostPCAPContentAnalysisHandler,
    HostProcessLogContentAnalysisHandler,
    HostProcessSummaryLogContentAnalysisHandler,
    HostSCContentAnalysisHandler,
    HostServiceLogContentAnalysisHandler,
    HostSocketSummaryLogContentAnalysisHandler,
    HostSyslogContentAnalysisHandler,
    HostSyslog1ContentAnalysisHandler,
    HostSyslog2ContentAnalysisHandler,
    HostSyslog3ContentAnalysisHandler,
    HostSyslog4ContentAnalysisHandler,
    HostSyslogLogContentAnalysisHandler,
    HostTXTContentAnalysisHandler,
    HostTestBSONContentAnalysisHandler,
    HostTestCSVContentAnalysisHandler,
    HostTestJSONContentAnalysisHandler,
    HostTestLogContentAnalysisHandler,
    HostTestNetflowDayContentAnalysisHandler,
    HostTestTXTContentAnalysisHandler,
    HostTestWLSDayContentAnalysisHandler,
    HostValidationCAPContentAnalysisHandler,
    HostValidationCSVContentAnalysisHandler,
    HostValidationJSONContentAnalysisHandler,
    HostValidationNetflowDayContentAnalysisHandler,
    HostValidationPCAPContentAnalysisHandler,
    HostValidationPCAPNGContentAnalysisHandler,
    HostValidationTXTContentAnalysisHandler,
    HostValidationWLSDayContentAnalysisHandler,
)

from rich.console import Console

from config import PATH_TEMP_DATA, PROJECT_ROOT,PATH_REPORT

console = Console()


def print_data(description, result):

    console.print(
        f"{description}\n"
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


def analyze_csv_content():

    handler = HostCSVContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host CSV content analysis completed.", result)


def analyze_auth_log_content():
    handler = HostAuthLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )

    result = handler.analyze_and_generate_docs()

    print_data("Host auth.log content analysis completed.", result)


def analyze_cpu_log_content():

    handler = HostCPULogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host cpu.log content analysis completed.", result)


def analyze_diskio_log_content():
    pass


def analyze_filesystem_log_content():
    pass


def analyze_fsstat_log_content():
    pass


def analyze_ghc_content():
    pass


def analyze_info_content():
    pass


def analyze_journal_content():
    pass


def analyze_journal_tilde_content():
    pass


def analyze_json_content():
    pass


def analyze_json_1_content():
    pass


def analyze_load_log_content():
    pass


def analyze_log_content():
    pass


def analyze_log_1_content():
    pass


def analyze_log_2_content():
    pass


def analyze_log_3_content():
    pass


def analyze_mail_info_1_content():
    pass


def analyze_mail_warn_1_content():
    pass


def analyze_mainlog_content():
    pass


def analyze_mainlog_1_content():
    pass


def analyze_mainlog_2_content():
    pass


def analyze_mainlog_3_content():
    pass


def analyze_memory_log_content():
    pass


def analyze_messages_content():
    pass


def analyze_messages_1_content():
    pass


def analyze_netflow_ids_content():
    pass


def analyze_network_log_content():
    pass


def analyze_pcap_content():
    pass


def analyze_process_log_content():
    pass


def analyze_process_summary_log_content():
    pass


def analyze_sc_content():
    pass


def analyze_service_log_content():
    pass


def analyze_socket_summary_log_content():
    pass


def analyze_syslog_content():
    pass


def analyze_syslog_1_content():
    pass


def analyze_syslog_2_content():
    pass


def analyze_syslog_3_content():
    pass


def analyze_syslog_4_content():
    pass


def analyze_syslog_log_content():
    pass


def analyze_test_bson_content():
    pass


def analyze_test_csv_content():
    pass


def analyze_test_json_content():
    pass


def analyze_test_log_content():
    pass


def analyze_test_netflow_day_content():
    pass


def analyze_test_txt_content():
    pass


def analyze_test_wls_day_content():
    pass


def analyze_validation_cap_content():
    pass


def analyze_validation_csv_content():
    pass


def analyze_validation_json_content():
    pass


def analyze_validation_netflow_day_content():
    pass


def analyze_validation_pcap_content():
    pass


def analyze_validation_pcapng_content():
    pass


def analyze_validation_txt_content():
    pass


def analyze_validation_wls_day_content():
    pass


def analyze_txt_content():
    pass


def analyze_uptime_log_content():
    pass


def analyze_xml_content():
    pass
