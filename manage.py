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

    if args.module == "handlers" and args.service == "host-analyze":
        return

    match (args.module, args.service, args.action):

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
