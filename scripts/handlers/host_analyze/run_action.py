from scripts.handlers.host_analyze import (
    HostAuthLogContentAnalysisHandler,
    HostCPULogContentAnalysisHandler,
    HostCSVContentAnalysisHandler,
    HostDiskioLogContentAnalysisHandler,
    HostFSStatLogContentAnalysisHandler,
    HostFilesystemLogContentAnalysisHandler,
    HostGHCContentAnalysisHandler,
    HostInfoContentAnalysisHandler,
    HostJSON1ContentAnalysisHandler,
    HostJSONContentAnalysisHandler,
    HostJournalContentAnalysisHandler,
    HostJournalTildeContentAnalysisHandler,
    HostLoadLogContentAnalysisHandler,
    HostLog1ContentAnalysisHandler,
    HostLog2ContentAnalysisHandler,
    HostLog3ContentAnalysisHandler,
    HostLogContentAnalysisHandler,
    HostMailInfo1ContentAnalysisHandler,
    HostMailWarn1ContentAnalysisHandler,
    HostMainlog1ContentAnalysisHandler,
    HostMainlog2ContentAnalysisHandler,
    HostMainlog3ContentAnalysisHandler,
    HostMainlogContentAnalysisHandler,
    HostMemoryLogContentAnalysisHandler,
    HostMessages1ContentAnalysisHandler,
    HostMessagesContentAnalysisHandler,
    HostNetflowIdsContentAnalysisHandler,
    HostNetworkLogContentAnalysisHandler,
    HostPCAPContentAnalysisHandler,
    HostProcessLogContentAnalysisHandler,
    HostProcessSummaryLogContentAnalysisHandler,
    HostSCContentAnalysisHandler,
    HostServiceLogContentAnalysisHandler,
    HostSocketSummaryLogContentAnalysisHandler,
    HostSyslog1ContentAnalysisHandler,
    HostSyslog2ContentAnalysisHandler,
    HostSyslog3ContentAnalysisHandler,
    HostSyslog4ContentAnalysisHandler,
    HostSyslogContentAnalysisHandler,
    HostSyslogLogContentAnalysisHandler,
    HostTXTContentAnalysisHandler,
    HostTestBSONContentAnalysisHandler,
    HostTestCSVContentAnalysisHandler,
    HostTestJSONContentAnalysisHandler,
    HostTestLogContentAnalysisHandler,
    HostTestNetflowDayContentAnalysisHandler,
    HostTestTXTContentAnalysisHandler,
    HostTestWLSDayContentAnalysisHandler,
    HostUptimeLogContentAnalysisHandler,
    HostValidationCAPContentAnalysisHandler,
    HostValidationCSVContentAnalysisHandler,
    HostValidationJSONContentAnalysisHandler,
    HostValidationNetflowDayContentAnalysisHandler,
    HostValidationPCAPContentAnalysisHandler,
    HostValidationPCAPNGContentAnalysisHandler,
    HostValidationTXTContentAnalysisHandler,
    HostValidationWLSDayContentAnalysisHandler,
    HostXMLContentAnalysisHandler,
)

from rich.console import Console

from config import PATH_REPORT, PATH_TEMP_DATA, PROJECT_ROOT


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
    handler = HostDiskioLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host diskio.log content analysis completed.", result)

def analyze_filesystem_log_content():
    handler = HostFilesystemLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host filesystem.log content analysis completed.", result)

def analyze_fsstat_log_content():
    handler = HostFSStatLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host fsstat.log content analysis completed.", result)

def analyze_ghc_content():
    handler = HostGHCContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host ghc content analysis completed.", result)

def analyze_info_content():
    handler = HostInfoContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host info content analysis completed.", result)

def analyze_journal_content():
    handler = HostJournalContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host journal content analysis completed.", result)

def analyze_journal_tilde_content():
    handler = HostJournalTildeContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host journal~ content analysis completed.", result)

def analyze_json_content():
    handler = HostJSONContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host json content analysis completed.", result)

def analyze_json_1_content():
    handler = HostJSON1ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host json-1 content analysis completed.", result)

def analyze_load_log_content():
    handler = HostLoadLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host load.log content analysis completed.", result)

def analyze_log_content():
    handler = HostLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host log content analysis completed.", result)

def analyze_log_1_content():
    handler = HostLog1ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host log-1 content analysis completed.", result)

def analyze_log_2_content():
    handler = HostLog2ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host log-2 content analysis completed.", result)

def analyze_log_3_content():
    handler = HostLog3ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host log-3 content analysis completed.", result)

def analyze_mail_info_1_content():
    handler = HostMailInfo1ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host mail-info-1 content analysis completed.", result)

def analyze_mail_warn_1_content():
    handler = HostMailWarn1ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host mail-warn-1 content analysis completed.", result)

def analyze_mainlog_content():
    handler = HostMainlogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host mainlog content analysis completed.", result)

def analyze_mainlog_1_content():
    handler = HostMainlog1ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host mainlog-1 content analysis completed.", result)

def analyze_mainlog_2_content():
    handler = HostMainlog2ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host mainlog-2 content analysis completed.", result)

def analyze_mainlog_3_content():
    handler = HostMainlog3ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host mainlog-3 content analysis completed.", result)

def analyze_memory_log_content():
    handler = HostMemoryLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host memory.log content analysis completed.", result)

def analyze_messages_content():
    handler = HostMessagesContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host messages content analysis completed.", result)

def analyze_messages_1_content():
    handler = HostMessages1ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host messages-1 content analysis completed.", result)

def analyze_netflow_ids_content():
    handler = HostNetflowIdsContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host netflow_ids content analysis completed.", result)

def analyze_network_log_content():
    handler = HostNetworkLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host network.log content analysis completed.", result)

def analyze_pcap_content():
    handler = HostPCAPContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host pcap content analysis completed.", result)

def analyze_process_log_content():
    handler = HostProcessLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host process.log content analysis completed.", result)

def analyze_process_summary_log_content():
    handler = HostProcessSummaryLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host process.summary.log content analysis completed.", result)

def analyze_sc_content():
    handler = HostSCContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host sc content analysis completed.", result)

def analyze_service_log_content():
    handler = HostServiceLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host service.log content analysis completed.", result)

def analyze_socket_summary_log_content():
    handler = HostSocketSummaryLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host socket.summary.log content analysis completed.", result)

def analyze_syslog_content():
    handler = HostSyslogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host syslog content analysis completed.", result)

def analyze_syslog_1_content():
    handler = HostSyslog1ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host syslog-1 content analysis completed.", result)

def analyze_syslog_2_content():
    handler = HostSyslog2ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host syslog-2 content analysis completed.", result)

def analyze_syslog_3_content():
    handler = HostSyslog3ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host syslog-3 content analysis completed.", result)

def analyze_syslog_4_content():
    handler = HostSyslog4ContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host syslog-4 content analysis completed.", result)

def analyze_syslog_log_content():
    handler = HostSyslogLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host syslog.log content analysis completed.", result)

def analyze_txt_content():
    handler = HostTXTContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host txt content analysis completed.", result)

def analyze_test_bson_content():
    handler = HostTestBSONContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host TEST bson content analysis completed.", result)

def analyze_test_csv_content():
    handler = HostTestCSVContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host TEST csv content analysis completed.", result)

def analyze_test_json_content():
    handler = HostTestJSONContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host TEST json content analysis completed.", result)

def analyze_test_log_content():
    handler = HostTestLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host TEST log content analysis completed.", result)

def analyze_test_netflow_day_content():
    handler = HostTestNetflowDayContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host TEST netflow_day content analysis completed.", result)

def analyze_test_txt_content():
    handler = HostTestTXTContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host TEST txt content analysis completed.", result)

def analyze_test_wls_day_content():
    handler = HostTestWLSDayContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host TEST wls_day content analysis completed.", result)

def analyze_validation_cap_content():
    handler = HostValidationCAPContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host VALIDATION cap content analysis completed.", result)

def analyze_validation_csv_content():
    handler = HostValidationCSVContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host VALIDATION csv content analysis completed.", result)

def analyze_validation_json_content():
    handler = HostValidationJSONContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host VALIDATION json content analysis completed.", result)

def analyze_validation_netflow_day_content():
    handler = HostValidationNetflowDayContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host VALIDATION netflow_day content analysis completed.", result)

def analyze_validation_pcap_content():
    handler = HostValidationPCAPContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host VALIDATION pcap content analysis completed.", result)

def analyze_validation_pcapng_content():
    handler = HostValidationPCAPNGContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host VALIDATION pcapng content analysis completed.", result)

def analyze_validation_txt_content():
    handler = HostValidationTXTContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host VALIDATION txt content analysis completed.", result)

def analyze_validation_wls_day_content():
    handler = HostValidationWLSDayContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host VALIDATION wls_day content analysis completed.", result)

def analyze_uptime_log_content():
    handler = HostUptimeLogContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host uptime.log content analysis completed.", result)

def analyze_xml_content():
    handler = HostXMLContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("Host xml content analysis completed.", result)
