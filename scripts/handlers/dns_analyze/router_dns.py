from rich.console import Console

from config import manage_commands
from scripts.handlers.dns_analyze.run_action import (
    analyze_train_csv_content,
    analyze_train_pcap_content,
    analyze_train_pcap_csv_content,
    analyze_test_csv_content,
    analyze_test_pcap_content,
    analyze_test_pcap_csv_content,
    analyze_validation_pcap_content,
    analyze_validation_txt_content
)

console = Console()

def router_dns(action: str):

    if action == "analyze-train-csv-content":

        analyze_train_csv_content()

    elif action == "analyze-train-pcap-content":

        analyze_train_pcap_content()

    elif action == "analyze-train-pcap-csv-content":

        analyze_train_pcap_csv_content()

    elif action == "analyze-test-csv-content":

        analyze_test_csv_content()

    elif action == "analyze-test-pcap-content":

        analyze_test_pcap_content()

    elif action == "analyze-test-pcap-csv-content":

        analyze_test_pcap_csv_content()

    elif action == "analyze-validation-pcap-content":

        analyze_validation_pcap_content()

    elif action == "analyze-validation-txt-content":

        analyze_validation_txt_content()

    else:
        print(manage_commands)