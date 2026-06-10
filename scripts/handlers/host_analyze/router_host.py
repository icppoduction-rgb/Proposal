from rich.console import Console

from config import manage_commands
from scripts.handlers.host_analyze.run_action import (
    analyze_auth_log_content,
    analyze_cpu_log_content,
    analyze_csv_content,
    analyze_diskio_log_content,
    analyze_filesystem_log_content,
    analyze_fsstat_log_content,
    analyze_ghc_content,
    analyze_info_content,
    analyze_journal_content,
    analyze_journal_tilde_content,
    analyze_json_1_content,
    analyze_json_content,
    analyze_load_log_content,
    analyze_log_1_content,
    analyze_log_2_content,
    analyze_log_3_content,
    analyze_log_content,
    analyze_mail_info_1_content,
    analyze_mail_warn_1_content,
    analyze_mainlog_1_content,
    analyze_mainlog_2_content,
    analyze_mainlog_3_content,
    analyze_mainlog_content,
    analyze_memory_log_content,
    analyze_messages_1_content,
    analyze_messages_content,
    analyze_netflow_ids_content,
    analyze_network_log_content,
    analyze_pcap_content,
    analyze_process_log_content,
    analyze_process_summary_log_content,
    analyze_sc_content,
    analyze_service_log_content,
    analyze_socket_summary_log_content,
    analyze_syslog_1_content,
    analyze_syslog_2_content,
    analyze_syslog_3_content,
    analyze_syslog_4_content,
    analyze_syslog_content,
    analyze_syslog_log_content,
    analyze_test_bson_content,
    analyze_test_csv_content,
    analyze_test_json_content,
    analyze_test_log_content,
    analyze_test_netflow_day_content,
    analyze_test_txt_content,
    analyze_test_wls_day_content,
    analyze_txt_content,
    analyze_uptime_log_content,
    analyze_validation_cap_content,
    analyze_validation_csv_content,
    analyze_validation_json_content,
    analyze_validation_netflow_day_content,
    analyze_validation_pcap_content,
    analyze_validation_pcapng_content,
    analyze_validation_txt_content,
    analyze_validation_wls_day_content,
    analyze_xml_content,
)


console = Console()


def router_host(action: str):
    if action == "analyze-csv-content":
        analyze_csv_content()

    elif action == "analyze-auth-log-content":
        analyze_auth_log_content()

    elif action == "analyze-cpu-log-content":
        analyze_cpu_log_content()

    elif action == "analyze-diskio-log-content":
        analyze_diskio_log_content()

    elif action == "analyze-filesystem-log-content":
        analyze_filesystem_log_content()

    elif action == "analyze-fsstat-log-content":
        analyze_fsstat_log_content()

    elif action == "analyze-ghc-content":
        analyze_ghc_content()

    elif action == "analyze-info-content":
        analyze_info_content()

    elif action == "analyze-journal-content":
        analyze_journal_content()

    elif action == "analyze-journal-tilde-content":
        analyze_journal_tilde_content()

    elif action == "analyze-json-content":
        analyze_json_content()

    elif action == "analyze-json-1-content":
        analyze_json_1_content()

    elif action == "analyze-load-log-content":
        analyze_load_log_content()

    elif action == "analyze-log-content":
        analyze_log_content()

    elif action == "analyze-log-1-content":
        analyze_log_1_content()

    elif action == "analyze-log-2-content":
        analyze_log_2_content()

    elif action == "analyze-log-3-content":
        analyze_log_3_content()

    elif action == "analyze-mail-info-1-content":
        analyze_mail_info_1_content()

    elif action == "analyze-mail-warn-1-content":
        analyze_mail_warn_1_content()

    elif action == "analyze-mainlog-content":
        analyze_mainlog_content()

    elif action == "analyze-mainlog-1-content":
        analyze_mainlog_1_content()

    elif action == "analyze-mainlog-2-content":
        analyze_mainlog_2_content()

    elif action == "analyze-mainlog-3-content":
        analyze_mainlog_3_content()

    elif action == "analyze-memory-log-content":
        analyze_memory_log_content()

    elif action == "analyze-messages-content":
        analyze_messages_content()

    elif action == "analyze-messages-1-content":
        analyze_messages_1_content()

    elif action == "analyze-netflow-ids-content":
        analyze_netflow_ids_content()

    elif action == "analyze-network-log-content":
        analyze_network_log_content()

    elif action == "analyze-pcap-content":
        analyze_pcap_content()

    elif action == "analyze-process-log-content":
        analyze_process_log_content()

    elif action == "analyze-process-summary-log-content":
        analyze_process_summary_log_content()

    elif action == "analyze-sc-content":
        analyze_sc_content()

    elif action == "analyze-service-log-content":
        analyze_service_log_content()

    elif action == "analyze-socket-summary-log-content":
        analyze_socket_summary_log_content()

    elif action == "analyze-syslog-content":
        analyze_syslog_content()

    elif action == "analyze-syslog-1-content":
        analyze_syslog_1_content()

    elif action == "analyze-syslog-2-content":
        analyze_syslog_2_content()

    elif action == "analyze-syslog-3-content":
        analyze_syslog_3_content()

    elif action == "analyze-syslog-4-content":
        analyze_syslog_4_content()

    elif action == "analyze-syslog-log-content":
        analyze_syslog_log_content()

    elif action == "analyze-test-bson-content":
        analyze_test_bson_content()

    elif action == "analyze-test-csv-content":
        analyze_test_csv_content()

    elif action == "analyze-test-json-content":
        analyze_test_json_content()

    elif action == "analyze-test-log-content":
        analyze_test_log_content()

    elif action == "analyze-test-netflow-day-content":
        analyze_test_netflow_day_content()

    elif action == "analyze-test-txt-content":
        analyze_test_txt_content()

    elif action == "analyze-test-wls-day-content":
        analyze_test_wls_day_content()

    elif action == "analyze-validation-cap-content":
        analyze_validation_cap_content()

    elif action == "analyze-validation-csv-content":
        analyze_validation_csv_content()

    elif action == "analyze-validation-json-content":
        analyze_validation_json_content()

    elif action == "analyze-validation-netflow-day-content":
        analyze_validation_netflow_day_content()

    elif action == "analyze-validation-pcap-content":
        analyze_validation_pcap_content()

    elif action == "analyze-validation-pcapng-content":
        analyze_validation_pcapng_content()

    elif action == "analyze-validation-txt-content":
        analyze_validation_txt_content()

    elif action == "analyze-validation-wls-day-content":
        analyze_validation_wls_day_content()

    elif action == "analyze-txt-content":
        analyze_txt_content()

    elif action == "analyze-uptime-log-content":
        analyze_uptime_log_content()

    elif action == "analyze-xml-content":
        analyze_xml_content()

    else:
        print(manage_commands)
