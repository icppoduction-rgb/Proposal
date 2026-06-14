# Handler: `dns_analyze`

## Purpose

`dns_analyze` analyzes DNS buckets prepared by `analyze_dataset -> sort -> save_sort`. Each action maps to a concrete role and data format.

## CLI

```powershell
python manage.py handlers dns-analyze <action>
```

## Components

| File | Purpose |
|---|---|
| `scripts/handlers/dns_analyze/router_dns.py` | Action -> analyzer class map. |
| `scripts/handlers/dns_analyze/run_action.py` | Shared analyzer execution and result printing. |
| `scripts/handlers/dns_analyze/analyze_dns_*_dataset_handler.py` | Concrete role/format bucket analyzers. |

## Inputs

| Artifact | Purpose |
|---|---|
| `PATH_TEMP_DATA/sort-path-dns-file.json` | `role -> format -> paths` map created by `save-sort-dns-dataset-handler`. |
| Files from the sorted tree | Actual DNS file contents analyzed by the concrete handler. |

## Supported Actions

| Role | Format/scope | Action | Handler file |
|---|---|---|---|
| TRAIN | csv | `analyze-train-csv-content` | `analyze_dns_train_csv_dataset_handler.py` |
| TRAIN | pcap | `analyze-train-pcap-content` | `analyze_dns_train_pcap_dataset_handler.py` |
| TRAIN | pcap.csv | `analyze-train-pcap-csv-content` | `analyze_dns_train_pcap_csv_dataset_handler.py` |
| TEST | csv | `analyze-test-csv-content` | `analyze_dns_test_csv_dataset_handler.py` |
| TEST | pcap | `analyze-test-pcap-content` | `analyze_dns_test_pcap_dataset_handler.py` |
| TEST | pcap.csv | `analyze-test-pcap-csv-content` | `analyze_dns_test_pcap_csv_dataset_handler.py` |
| VALIDATION | pcap | `analyze-validation-pcap-content` | `analyze_dns_validation_pcap_dataset_handler.py` |
| VALIDATION | txt | `analyze-validation-txt-content` | `analyze_dns_validation_txt_dataset_handler.py` |

## Outputs

Each analyzer creates a summary JSON in `PATH_TEMP_DATA` and Markdown/text reports in docs/report directories from `config.py`. Summary names follow:

```text
analysis-dns-<role>-<format>-summary.json
```

Examples:

| Action | Summary |
|---|---|
| `analyze-train-csv-content` | `analysis-dns-train-csv-summary.json` |
| `analyze-test-pcap-content` | `analysis-dns-test-pcap-summary.json` |
| `analyze-validation-txt-content` | `analysis-dns-validation-txt-summary.json` |

A typical summary contains source JSON path, role, format, scope/counters, status, detected schema/content information, and a blocking reason when analysis cannot proceed.

## Pipeline Position

```text
DNS source files
  -> analyze-dataset dns-dataset-handler
  -> sort sort-dns-dataset-handler
  -> save-sort save-sort-dns-dataset-handler
  -> dns-analyze <role/format action>
```

`dns_analyze` does not write the PostgreSQL Catalog and does not create normalized Parquet. Its purpose is exploratory/documentation preparation before Stage Two parsers.

## Constraints

- An action must be explicitly registered in `router_dns.py`.
- If `sort-path-dns-file.json` does not contain the required bucket, the concrete handler may finish with a blocking summary.
- The DNS content-analyzer set is not the same as the Stage Two parser set. Stage Two active parser entries are controlled by `parser_registry_seed.json` and resolver logic.
