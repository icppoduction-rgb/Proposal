# Handlers Architecture: dns_analyze

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Package Files](#2-package-files)
- [3. Service Startup](#3-service-startup)
- [4. General Call Chain](#4-general-call-chain)
- [5. Router and run_action](#5-router-and-run_action)
- [6. Common Content-Analysis Handler Contract](#6-common-content-analysis-handler-contract)
- [7. DNS TRAIN Handlers](#7-dns-train-handlers)
- [8. DNS TEST Handlers](#8-dns-test-handlers)
- [9. DNS VALIDATION Handlers](#9-dns-validation-handlers)
- [10. Output Artifacts](#10-output-artifacts)
- [11. Errors and Limitations](#11-errors-and-limitations)

## 1. Purpose

`scripts/handlers/dns_analyze` analyzes DNS file contents after sorting and path export. The service reads `sort-path-dns-file.json`, selects a specific role and format, builds summary JSON, and generates bilingual markdown documentation.

This service is the final stage of the DNS pipeline.

## 2. Package Files

| File | Purpose |
|---|---|
| `router_dns.py` | Routes DNS analysis actions. |
| `run_action.py` | Instantiates handler classes and prints results. |
| `__init__.py` | Exports DNS content-analysis handler classes. |
| `analyze_dns_train_csv_dataset_handler.py` | Analyzes `TRAIN/csv`. |
| `analyze_dns_train_pcap_dataset_handler.py` | Analyzes `TRAIN/pcap`. |
| `analyze_dns_train_pcap_csv_dataset_handler.py` | Analyzes `TRAIN/pcap.csv`. |
| `analyze_dns_test_csv_dataset_handler.py` | Analyzes `TEST/csv`. |
| `analyze_dns_test_pcap_dataset_handler.py` | Analyzes `TEST/pcap`. |
| `analyze_dns_test_pcap_csv_dataset_handler.py` | Analyzes `TEST/pcap.csv`. |
| `analyze_dns_validation_pcap_dataset_handler.py` | Analyzes `VALIDATION/pcap`. |
| `analyze_dns_validation_txt_dataset_handler.py` | Analyzes `VALIDATION/txt`. |

## 3. Service Startup

Format:

```bash
python manage.py handlers dns-analyze <action>
```

Before running, this file must exist:

```text
PATH_TEMP_DATA/sort-path-dns-file.json
```

It is normally created by:

```bash
python manage.py handlers save-sort save-sort-dns-dataset-handler
```

## 4. General Call Chain

```text
python manage.py handlers dns-analyze <action>
-> manage.manage()
-> router_commands("handlers", "dns-analyze", action)
-> router_commands_handlers("dns-analyze", action)
-> router_dns(action)
-> analyze_*_content()
-> DNS*ContentAnalysisHandler(PATH_TEMP_DATA, PROJECT_ROOT, PATH_REPORT)
-> analyze_and_generate_docs()
-> _read_source_json()
-> _extract_paths(...)
-> _select_sample_paths(...)                 # when sampling is used
-> _build_summary(...)
-> JsonDataManager(summary_json).write(...)
-> _build_markdown(...) / _build_readme(...) / _build_report(...)
-> _write_text_file(...)
-> print_data(...)
```

## 5. Router and run_action

### `router_dns(action: str)`

| Action | Run function |
|---|---|
| `analyze-train-csv-content` | `analyze_train_csv_content()` |
| `analyze-train-pcap-content` | `analyze_train_pcap_content()` |
| `analyze-train-pcap-csv-content` | `analyze_train_pcap_csv_content()` |
| `analyze-test-csv-content` | `analyze_test_csv_content()` |
| `analyze-test-pcap-content` | `analyze_test_pcap_content()` |
| `analyze-test-pcap-csv-content` | `analyze_test_pcap_csv_content()` |
| `analyze-validation-pcap-content` | `analyze_validation_pcap_content()` |
| `analyze-validation-txt-content` | `analyze_validation_txt_content()` |

Unknown actions print `manage_commands`.

### `run_action.py`

Each function:

1. Instantiates the handler class.
2. Passes `PATH_TEMP_DATA`, `PROJECT_ROOT`, and `PATH_REPORT`.
3. Calls `analyze_and_generate_docs()`.
4. Passes the result to `print_data()`.

`print_data(description, result)` prints:

- summary JSON;
- RU/EN docs;
- RU/EN README;
- RU/EN reports;
- total/sample counts;
- status.

## 6. Common Content-Analysis Handler Contract

Most DNS handlers follow the same template.

### Input

```text
PATH_TEMP_DATA/sort-path-dns-file.json
```

Shape:

```json
{
  "TRAIN": {
    "csv": ["/absolute/path/file.csv"]
  }
}
```

### Main Method

`analyze_and_generate_docs()`:

1. Reads source JSON.
2. Extracts paths for a fixed role and format.
3. Selects a sample if the dataset exceeds the configured limit.
4. Builds summary.
5. Writes summary JSON to `PATH_TEMP_DATA`.
6. Writes RU/EN markdown docs under `docs/...`.
7. Writes RU/EN `README.md`.
8. Writes RU/EN reports under `PATH_REPORT`.
9. Returns a result dataclass.

### Typical Helper Methods

| Method | Purpose |
|---|---|
| `_read_source_json()` | Reads `sort-path-dns-file.json`. |
| `_extract_paths(...)` | Returns paths for the target role/format. |
| `_select_sample_paths(...)` | Selects an evenly spread file sample. |
| `_build_summary(...)` | Builds technical summary data. |
| `_build_markdown(...)` | Generates format documentation. |
| `_build_readme(...)` | Generates directory index. |
| `_build_report(...)` | Generates report. |
| `_load_counts()` | Reads format counts when needed for README. |
| `_load_optional_status()` | Reads another summary status when needed. |
| `_summary_json_excerpt()` | Builds a short JSON excerpt for reports. |
| `_write_text_file(...)` | Creates directory and writes markdown. |

## 7. DNS TRAIN Handlers

### `DNSTrainCSVContentAnalysisHandler`

File:

- `analyze_dns_train_csv_dataset_handler.py`

Purpose: analyzes `TRAIN/csv` files containing tabular domain/DNS features.

Classes:

| Class | Purpose |
|---|---|
| `DNSTrainCSVContentAnalysisResult` | Summary/docs/reports generation result. |
| `CSVProbe` | Technical probe for one CSV file. |
| `DNSTrainCSVContentAnalysisHandler` | Main handler. |

Important methods:

- `_probe_file()` reads CSV, detects header, row count, column distribution, and parse errors.
- `_schema_kind()` classifies schema type.
- `_class_hint()` extracts a class hint from name/path.
- `_infer_type()` infers value type.
- `_fields_table()` renders a markdown field table.

### `DNSTrainPCAPContentAnalysisHandler`

File:

- `analyze_dns_train_pcap_dataset_handler.py`

Purpose: analyzes `TRAIN/pcap` packet capture files.

Classes:

- `DNSTrainPCAPContentAnalysisResult`;
- `DNSPCAPProbe`;
- `DNSTrainPCAPContentAnalysisHandler`.

Important methods:

- `_probe_file()` collects technical PCAP attributes;
- `_build_summary()` determines status and feature-extraction readiness;
- `_load_optional_status()` loads additional status data for indexes.

### `DNSTrainPCAPCSVContentAnalysisHandler`

File:

- `analyze_dns_train_pcap_csv_dataset_handler.py`

Purpose: analyzes CSV derivatives from PCAP (`TRAIN/pcap.csv`).

Classes:

- `DNSTrainPCAPCSVContentAnalysisResult`;
- `PCAPCSVProbe`;
- `DNSTrainPCAPCSVContentAnalysisHandler`.

Important methods:

- `_probe_csv()` analyzes rows and columns;
- `_field_summaries()` collects field details;
- `_class_hint()` helps infer class from file name.

## 8. DNS TEST Handlers

### `DNSTestCSVContentAnalysisHandler`

File:

- `analyze_dns_test_csv_dataset_handler.py`

Purpose: analyzes `TEST/csv` data for inference-readiness checks.

Classes:

- `DNSTestCSVContentAnalysisResult`;
- `DNSTestCSVProbe`;
- `DNSTestCSVContentAnalysisHandler`.

Notes:

- uses `_probe_csv()` and `_field_summaries()`;
- builds status for test CSV;
- generates README and reports for TEST docs.

### `DNSTestPCAPContentAnalysisHandler`

File:

- `analyze_dns_test_pcap_dataset_handler.py`

Purpose: describes `TEST/pcap`. If files are missing or empty, it generates `BROKEN_OR_EMPTY` status.

### `DNSTestPCAPCSVContentAnalysisHandler`

File:

- `analyze_dns_test_pcap_csv_dataset_handler.py`

Purpose: describes `TEST/pcap.csv`, including empty or missing dataset cases.

## 9. DNS VALIDATION Handlers

### `DNSValidationPCAPContentAnalysisHandler`

File:

- `analyze_dns_validation_pcap_dataset_handler.py`

Inherits from:

```text
DNSTrainPCAPContentAnalysisHandler
```

Purpose: reuses train PCAP analysis logic, but changes role, documentation directories, and report text for `VALIDATION/pcap`.

Key methods:

- `analyze_and_generate_docs()`;
- `_build_validation_markdown()`;
- `_build_validation_readme()`;
- `_build_validation_report()`;
- `_label_values()`.

### `DNSValidationTXTContentAnalysisHandler`

File:

- `analyze_dns_validation_txt_dataset_handler.py`

Purpose: analyzes `VALIDATION/txt`, checking domain-like lines and class hints.

Classes:

- `DNSValidationTXTContentAnalysisResult`;
- `DNSTXTProbe`;
- `DNSValidationTXTContentAnalysisHandler`.

Important methods:

- `_probe_txt()` reads and classifies text lines;
- `_is_domain_like()` checks whether a line looks like a domain;
- `_class_hint()` extracts class from path/name.

## 10. Output Artifacts

Each handler returns a dataclass with:

- `summary_json_file`;
- `docs_ru_file`;
- `docs_en_file`;
- `docs_ru_readme_file`;
- `docs_en_readme_file`;
- `report_ru_file`;
- `report_en_file`;
- `total_files_count`;
- `sampled_files_count`;
- `status`.

Typical paths:

```text
PATH_TEMP_DATA/analysis-dns-*-summary.json
docs/ru/analysis-dataset/dns/<role>/<format>.md
docs/en/analysis-dataset/dns/<role>/<format>.md
PATH_REPORT/ru/stage-one/analysis-dataset/dns/<role>/*.md
PATH_REPORT/en/stage-one/analysis-dataset/dns/<role>/*.md
```

## 11. Errors and Limitations

- All DNS analysis routes depend on `sort-path-dns-file.json`.
- If the JSON lacks the target role or format, handlers either raise `ValueError` or report an empty dataset in summary, depending on implementation.
- Sampling limits analysis depth for large datasets.
- PCAP handlers provide technical overview, not a full packet parser replacement.
- Adding a new format requires changes in a handler file, `__init__.py`, `run_action.py`, `router_dns.py`, and `manage_commands`.
