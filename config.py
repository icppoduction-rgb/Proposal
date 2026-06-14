import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------- PATHS FOLDERS ---------------------- #

load_dotenv()

PROJECT_ROOT: Path = Path(__file__).resolve().parent


def _child_path(root: str, child: str) -> str:
    """Build a child path only when the parent path is configured."""
    root = root.strip()
    if not root:
        return ""
    return str(Path(root).expanduser() / child)


PATH_DATA_STORAGE: str = os.getenv("PATH_DATA_STORAGE", "")

PATH_FOLDER_DATASETS: str = os.getenv("PATH_FOLDER_DATASETS", "")

PATH_FOLDER_DATASETS_FILTER: str = os.getenv("PATH_FOLDER_DATASETS_FILTER", "")

PATH_HOST_DATASETS: str = f'{PATH_FOLDER_DATASETS}/host'
PATH_DNS_DATASETS: str = f"{PATH_FOLDER_DATASETS}/dns"

PATH_HOST_DATASETS_FILTER: str = f'{PATH_FOLDER_DATASETS_FILTER}/host'
PATH_DNS_DATASETS_FILTER: str = f'{PATH_FOLDER_DATASETS_FILTER}/dns'

PATH_REPORT: str = f'{PATH_DATA_STORAGE}/reports'
PATH_TEMP_DATA: str = f'{PATH_DATA_STORAGE}/temp_data'
PATH_FILTER_LOG = f"{PATH_DATA_STORAGE}/logs/filter_log",

# ------------------------ PATH CONFIG -------------------------------- #

CONFIG_PATH: str = f"{PATH_DATA_STORAGE}/config"

# --------------------------- PATH DUCKDB ----------------------------- #

DUCKDB_PATH: str = f"{PATH_DATA_STORAGE}/duckdb"

EXPORTS_PATH: str = f"{DUCKDB_PATH}/exports"

SQL_PATH: str = f"{DUCKDB_PATH}/sql"

# --------------------------- PATH PARQUET ---------------------------- #

PARQUET_PATH: str = f"{PATH_DATA_STORAGE}/parquet"

FEATURES_PATH: str = f"{PARQUET_PATH}/features"

MODELS_READY: str = f"{PARQUET_PATH}/models_ready"

NORMALIZED: str = f"{PARQUET_PATH}/normalized"

# -------------------------- PATH REPORT ------------------------------ #

EN_PATH_REPORT: str = f"{PATH_REPORT}/en"
RU_PATH_REPORT: str = f"{PATH_REPORT}/ru"

STAGE_TWO_EN: str = f"{EN_PATH_REPORT}/stage-two"

STAGE_TWO_RU: str = f"{EN_PATH_REPORT}/stage-two"

# ---------------------- PATH FILE TEMP_DATA -------------------------- #

PATH_TEMP_DATA_DNS: str = f'{PATH_TEMP_DATA}/dns'

ANALYSIS_DNS_TEST_CSV_SUMMARY: str = f'{PATH_TEMP_DATA_DNS}/test/analysis-dns-test-csv-summary.json'
ANALYSIS_DNS_TEST_PCAP_CSV_SUMMARY: str = f'{PATH_TEMP_DATA_DNS}/test/analysis-dns-test-pcap-csv-summary.json'
ANALYSIS_DNS_TEST_PCAP_SUMMARY: str = f'{PATH_TEMP_DATA_DNS}/test/analysis-dns-test-pcap-summary.json'

ANALYSIS_DNS_TRAIN_CSV_SUMMARY: str = f'{PATH_TEMP_DATA_DNS}/train/analysis-dns-train-csv-summary.json'
ANALYSIS_DNS_TRAIN_PCAP_CSV_SUMMARY: str = f'{PATH_TEMP_DATA_DNS}/train/analysis-dns-train-pcap-csv-summary.json'
ANALYSIS_DNS_TRAIN_PCAP_SUMMARY: str = f'{PATH_TEMP_DATA_DNS}/tain/analysis-dns-train-pcap-summary.json'

ANALYSIS_DNS_VALIDATION_PCAP_SUMMARY: str = f'{PATH_TEMP_DATA_DNS}/validation/analysis-dns-validation-pcap-summary.json'
ANALYSIS_DNS_VALIDATION_TXT_SUMMARY: str = f'{PATH_TEMP_DATA_DNS}/validationanalysis-dns-validation-txt-summary.json'

# Общий путь к host
PATH_TEMP_DATA_HOST: str = f'{PATH_TEMP_DATA}/host'

# Общий пути к проанализированы файлам
PATH_TEMP_DATA_HOST_TRAIN: str = f'{PATH_TEMP_DATA_HOST}/train'
PATH_TEMP_DATA_HOST_TEST: str = f'{PATH_TEMP_DATA_HOST}/test'
PATH_TEMP_DATA_HOST_VALIDATION: str = f'{PATH_TEMP_DATA_HOST}/validation'

ANALYSIS_HOST_CSV_SUMMARY: str = f'{PATH_TEMP_DATA}/analysis-host-csv-summary.json'

DNS_FILE: str = f'{PATH_DATA_STORAGE}/dns-file.json'
DNS_PATH_FILE: str = f'{PATH_DATA_STORAGE}/dns-path-file.json'
SORT_DNS_FORMAT_SUMMARY: str = f'{PATH_DATA_STORAGE}/sort-dns-format-summary.json'
SORT_PATH_DNS_FILE: str = f'{PATH_DATA_STORAGE}/sort-path-dns-file.json'
SORT_PATH_DNS_FILE_SUMMARY: str = f'{PATH_DATA_STORAGE}/sort-path-dns-file-summary.json'

HOST_FILE: str = f'{PATH_DATA_STORAGE}/host-file.json'
HOST_PATH_FILE: str = f'{PATH_DATA_STORAGE}/host-path-file.json'
FILTER_HOST_FILE: str = f'{PATH_DATA_STORAGE}/filter-host-file.json'
FILTER_HOST_PATH_FILE: str = f'{PATH_DATA_STORAGE}/filter-host-path-file.json'
SORT_HOST_FORMAT_SUMMARY: str = f'{PATH_DATA_STORAGE}/sort-host-format-summary.json'
SORT_PATH_HOST_FILE: str = f'{PATH_DATA_STORAGE}/sort-path-host-file.json'
SORT_PATH_HOST_FILE_SUMMARY: str = f'{PATH_DATA_STORAGE}/sort-path-host-file-summary.json'

# --------------------------- PATH DOCS ------------------------------- #

DOCS_EN_ANALYSIS_HOST_TRAIN: str = "docs/en/analysis-dataset/host/train"
DOCS_RU_ANALYSIS_HOST_TRAIN: str = "docs/ru/analysis-dataset/host/train"

DOCS_EN_ANALYSIS_HOST_TEST: str = "docs/en/analysis-dataset/host/test"
DOCS_RU_ANALYSIS_HOST_TEST: str = "docs/ru/analysis-dataset/host/test"

DOCS_EN_ANALYSIS_HOST_VALIDATION: str = "docs/en/analysis-dataset/host/validation"
DOCS_RU_ANALYSIS_HOST_VALIDATION: str = "docs/ru/analysis-dataset/host/validation"

DOCS_EN_ANALYSIS_DNS_TRAIN: str = "docs/en/analysis-dataset/dns/train"
DOCS_RU_ANALYSIS_DNS_TRAIN: str = "docs/ru/analysis-dataset/host/train"

DOCS_EN_ANALYSIS_DNS_TEST: str = "docs/en/analysis-dataset/dns/test"
DOCS_RU_ANALYSIS_DNS_TEST: str = "docs/ru/analysis-dataset/dns/test"

DOCS_EN_ANALYSIS_DNS_VALIDATION: str = "docs/en/analysis-dataset/dns/validation"
DOCS_RU_ANALYSIS_DNS_VALIDATION: str = "docs/ru/analysis-dataset/dns/validation"

# --------------------------- PATH REPORT ------------------------------- #

REPORTS_EN_STAGE_ONE_ANALYSIS_HOST_TRAIN: str = "en/stage-one/analysis-dataset/host/train"
REPORTS_RU_STAGE_ONE_ANALYSIS_HOST_TRAIN: str = "ru/stage-one/analysis-dataset/host/train"

REPORTS_EN_STAGE_ONE_ANALYSIS_HOST_TEST: str = "en/stage-one/analysis-dataset/host/test"
REPORTS_RU_STAGE_ONE_ANALYSIS_HOST_TEST: str = "ru/stage-one/analysis-dataset/host/test"

REPORTS_EN_STAGE_ONE_ANALYSIS_HOST_VALIDATION: str = "en/stage-one/analysis-dataset/host/validation"
REPORTS_RU_STAGE_ONE_ANALYSIS_HOST_VALIDATION: str = "ru/stage-one/analysis-dataset/host/validation"

REPORTS_EN_STAGE_ONE_ANALYSIS_DNS_TRAIN: str = "en/stage-one/analysis-dataset/dns/train"
REPORTS_RU_STAGE_ONE_ANALYSIS_DNS_TRAIN: str = "ru/stage-one/analysis-dataset/dns/train"

REPORTS_EN_STAGE_ONE_ANALYSIS_DNS_TEST: str = "en/stage-one/analysis-dataset/dns/test"
REPORTS_RU_STAGE_ONE_ANALYSIS_DNS_TEST: str = "ru/stage-one/analysis-dataset/dns/test"

REPORTS_EN_STAGE_ONE_ANALYSIS_DNS_VALIDATION: str = "en/stage-one/analysis-dataset/dns/validation"
REPORTS_RU_STAGE_ONE_ANALYSIS_DNS_VALIDATION: str = "ru/stage-one/analysis-dataset/dns/validation"



# ----------------------------------------------------------------

manage_commands: str = (
    "Commands:\n"
    "# ===================== HANDLERS COMMAND ========================= #\n"
    "\n"
    "# ----------------------- Analyze Dataset ------------------------ #\n"
    "\n"
    "python manage.py handlers analyze-dataset host-dataset-handler\n"
    "python manage.py handlers analyze-dataset dns-dataset-handler\n"
    "\n"
    "# ------------------------- Sort -------------------------------- #\n"
    "\n"
    "python manage.py handlers sort sort-dns-dataset-handler\n"
    "python manage.py handlers sort sort-host-dataset-handler\n"
    "\n"
    "# ------------------------ Save Sort ---------------------------- #\n"
    "\n"
    "python manage.py handlers save-sort save-sort-dns-dataset-handler\n"
    "python manage.py handlers save-sort save-sort-host-dataset-handler\n"
    "\n"
    "# -------------------------- Filter Dataset --------------------- #\n"
    "\n"
    "python manage.py handlers filter-dataset filter-host-dataset-handler\n"
    "\n"
    "# ---------------------------- DNS Analyze ------------------------ #\n"
    "\n"
    "python manage.py handlers dns-analyze analyze-train-csv-content\n"
    "python manage.py handlers dns-analyze analyze-train-pcap-content\n"
    "python manage.py handlers dns-analyze analyze-train-pcap-csv-content\n"
    "python manage.py handlers dns-analyze analyze-test-csv-content\n"
    "python manage.py handlers dns-analyze analyze-test-pcap-content\n"
    "python manage.py handlers dns-analyze analyze-test-pcap-csv-content\n"
    "python manage.py handlers dns-analyze analyze-validation-pcap-content\n"
    "python manage.py handlers dns-analyze analyze-validation-txt-content\n"
    "\n"
    "# ------------------------- Host Analyze --------------------------- #\n"
    "\n"
    "python manage.py handlers host-analyze analyze-csv-content\n"
    "python manage.py handlers host-analyze analyze-auth-log-content\n"
    "python manage.py handlers host-analyze analyze-cpu-log-content\n"
    "python manage.py handlers host-analyze analyze-diskio-log-content\n"
    "python manage.py handlers host-analyze analyze-filesystem-log-content\n"
    "python manage.py handlers host-analyze analyze-fsstat-log-content\n"
    "python manage.py handlers host-analyze analyze-ghc-content\n"
    "python manage.py handlers host-analyze analyze-info-content\n"
    "python manage.py handlers host-analyze analyze-journal-content\n"
    "python manage.py handlers host-analyze analyze-journal-tilde-content\n"
    "python manage.py handlers host-analyze analyze-json-content\n"
    "python manage.py handlers host-analyze analyze-json-1-content\n"
    "python manage.py handlers host-analyze analyze-load-log-content\n"
    "python manage.py handlers host-analyze analyze-log-content\n"
    "python manage.py handlers host-analyze analyze-log-1-content\n"
    "python manage.py handlers host-analyze analyze-log-2-content\n"
    "python manage.py handlers host-analyze analyze-log-3-content\n"
    "python manage.py handlers host-analyze analyze-mail-info-1-content\n"
    "python manage.py handlers host-analyze analyze-mail-warn-1-content\n"
    "python manage.py handlers host-analyze analyze-mainlog-content\n"
    "python manage.py handlers host-analyze analyze-mainlog-1-content\n"
    "python manage.py handlers host-analyze analyze-mainlog-2-content\n"
    "python manage.py handlers host-analyze analyze-mainlog-3-content\n"
    "python manage.py handlers host-analyze analyze-memory-log-content\n"
    "python manage.py handlers host-analyze analyze-messages-content\n"
    "python manage.py handlers host-analyze analyze-messages-1-content\n"
    "python manage.py handlers host-analyze analyze-netflow-ids-content\n"
    "python manage.py handlers host-analyze analyze-network-log-content\n"
    "python manage.py handlers host-analyze analyze-pcap-content\n"
    "python manage.py handlers host-analyze analyze-process-log-content\n"
    "python manage.py handlers host-analyze analyze-process-summary-log-content\n"
    "python manage.py handlers host-analyze analyze-sc-content\n"
    "python manage.py handlers host-analyze analyze-service-log-content\n"
    "python manage.py handlers host-analyze analyze-socket-summary-log-content\n"
    "python manage.py handlers host-analyze analyze-syslog-content\n"
    "python manage.py handlers host-analyze analyze-syslog-1-content\n"
    "python manage.py handlers host-analyze analyze-syslog-2-content\n"
    "python manage.py handlers host-analyze analyze-syslog-3-content\n"
    "python manage.py handlers host-analyze analyze-syslog-4-content\n"
    "python manage.py handlers host-analyze analyze-syslog-log-content\n"
    "python manage.py handlers host-analyze analyze-test-bson-content\n"
    "python manage.py handlers host-analyze analyze-test-csv-content\n"
    "python manage.py handlers host-analyze analyze-test-json-content\n"
    "python manage.py handlers host-analyze analyze-test-log-content\n"
    "python manage.py handlers host-analyze analyze-test-netflow-day-content\n"
    "python manage.py handlers host-analyze analyze-test-txt-content\n"
    "python manage.py handlers host-analyze analyze-test-wls-day-content\n"
    "python manage.py handlers host-analyze analyze-validation-cap-content\n"
    "python manage.py handlers host-analyze analyze-validation-csv-content\n"
    "python manage.py handlers host-analyze analyze-validation-json-content\n"
    "python manage.py handlers host-analyze analyze-validation-netflow-day-content\n"
    "python manage.py handlers host-analyze analyze-validation-pcap-content\n"
    "python manage.py handlers host-analyze analyze-validation-pcapng-content\n"
    "python manage.py handlers host-analyze analyze-validation-txt-content\n"
    "python manage.py handlers host-analyze analyze-validation-wls-day-content\n"
    "python manage.py handlers host-analyze analyze-txt-content\n"
    "python manage.py handlers host-analyze analyze-uptime-log-content\n"
    "python manage.py handlers host-analyze analyze-xml-content\n"
    "\n"
    "# ------------------------- Stage Two ----------------------------- #\n"
    "\n"
    "python manage.py stage-two bootstrap-storage\n"
    "python manage.py stage-two catalog-ingest\n"
    "python manage.py stage-two seed-parser-registry\n"
    "python manage.py stage-two normalize-dns\n"
    "python manage.py stage-two normalize-host\n"
    "python manage.py stage-two run-duckdb-checks\n"
    "python manage.py stage-two run-leakage-checks\n"
    "python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>\n"
)
