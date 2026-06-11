from scripts.handlers.dns_analyze import (
    DNSTrainCSVContentAnalysisHandler,
    DNSTrainPCAPContentAnalysisHandler,
    DNSTrainPCAPCSVContentAnalysisHandler,
    DNSTestCSVContentAnalysisHandler,
    DNSTestPCAPContentAnalysisHandler,
    DNSTestPCAPCSVContentAnalysisHandler,
    DNSValidationPCAPContentAnalysisHandler,
    DNSValidationTXTContentAnalysisHandler
)

from rich.console import Console
from config import PATH_TEMP_DATA, PROJECT_ROOT, PATH_REPORT

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


def analyze_train_csv_content():

    handler = DNSTrainCSVContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )

    result = handler.analyze_and_generate_docs()

    print_data("DNS TRAIN csv content analysis completed.", result)

def analyze_train_pcap_content():

    handler = DNSTrainPCAPContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )

    result = handler.analyze_and_generate_docs()

    print_data("DNS TRAIN pcap content analysis completed.", result)


def analyze_train_pcap_csv_content():

    handler = DNSTrainPCAPCSVContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("DNS TRAIN pcap.csv content analysis completed.", result)


def analyze_test_csv_content():

    handler = DNSTestCSVContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("DNS TEST csv content analysis completed.", result)


def analyze_test_pcap_content():

    handler = DNSTestPCAPContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("DNS TEST pcap content analysis completed.", result)


def analyze_test_pcap_csv_content():

    handler = DNSTestPCAPCSVContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("DNS TEST pcap.csv content analysis completed.", result)


def analyze_validation_pcap_content():

    handler = DNSValidationPCAPContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("DNS VALIDATION pcap content analysis completed.", result)

def analyze_validation_txt_content():
    handler = DNSValidationTXTContentAnalysisHandler(
        temp_data_path=PATH_TEMP_DATA,
        project_root=PROJECT_ROOT,
        report_path=PATH_REPORT,
    )
    result = handler.analyze_and_generate_docs()

    print_data("DNS VALIDATION txt content analysis completed.", result)