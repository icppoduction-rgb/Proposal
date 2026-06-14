# Pipeline, Artifacts, and Data Contracts

## Stage One Call Order

### DNS

| Step | Command | Input | Output |
|---|---|---|---|
| 1 | `handlers analyze-dataset dns-dataset-handler` | `PATH_DNS_DATASETS` | `PATH_TEMP_DATA/dns-path-file.json`, `PATH_TEMP_DATA/dns-file.json` |
| 2 | `handlers sort sort-dns-dataset-handler` | `dns-path-file.json`, `dns-file.json` | sorted tree in `PATH_DNS_DATASETS_FILTER`, `sort-dns-format-summary.json` |
| 3 | `handlers save-sort save-sort-dns-dataset-handler` | `PATH_DNS_DATASETS_FILTER` | `sort-path-dns-file.json`, `sort-path-dns-file-summary.json` |
| 4 | `handlers dns-analyze <action>` | `sort-path-dns-file.json`, sorted files | `analysis-dns-*-summary.json`, Markdown/report files |

### Host

| Step | Command | Input | Output |
|---|---|---|---|
| 1 | `handlers analyze-dataset host-dataset-handler` | `PATH_HOST_DATASETS` | `host-path-file.json`, `host-file.json` |
| 2 | `handlers filter-dataset filter-host-dataset-handler` | `host-path-file.json`, `host-file.json` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`, filter log |
| 3 | `handlers sort sort-host-dataset-handler` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json` | sorted tree in `PATH_HOST_DATASETS_FILTER`, `sort-host-format-summary.json` |
| 4 | `handlers save-sort save-sort-host-dataset-handler` | `PATH_HOST_DATASETS_FILTER` | `sort-path-host-file.json`, `sort-path-host-file-summary.json` |
| 5 | `handlers host-analyze <action>` | `sort-path-host-file.json`, sorted files | `analysis-host-*-summary.json`, Markdown/report files |

## Stage Two Call Order

| Step | Command | Input | Output |
|---|---|---|---|
| 1 | `stage-two bootstrap-storage` | `PATH_DATA_STORAGE` | Required storage directories. |
| 2 | `stage-two catalog-ingest` | configured raw/filter roots | `ingestion_runs`, `datasets`, `dataset_files`. |
| 3 | `stage-two seed-parser-registry` | schema JSON, seed JSON | `schema_versions`, `parser_registry`. |
| 4 | operational status update | catalog rows | `dataset_files.status = READY_FOR_PARSING` for files selected for parsing. No public CLI command exists today. |
| 5 | `stage-two normalize-dns [limit]` / `normalize-host [limit]` | READY catalog files, active parser registry | normalized Parquet, `parser_runs`, `normalized_artifacts`. |
| 6 | feature/model-ready APIs | normalized artifacts | feature/model-ready Parquet and catalog rows. No general CLI command exists today. |
| 7 | `stage-two run-duckdb-checks` / `run-leakage-checks` | Parquet/catalog metadata | JSON reports, `data_quality_reports`. |
| 8 | `stage-two trace-artifact <id-or-path>` | model-ready artifact ID/path | JSON traceability chain. |

## Temporary Stage One JSON

### Discovery JSON

```json
{
  "TRAIN": ["path-or-file-name"],
  "VALIDATION": ["path-or-file-name"],
  "TEST": ["path-or-file-name"]
}
```

Used by:

| File | Element meaning | Readers |
|---|---|---|
| `dns-path-file.json` | DNS paths | DNS sorter |
| `dns-file.json` | DNS file names | DNS sorter |
| `host-path-file.json` | Host paths | Host filter |
| `host-file.json` | Host file names | Host filter |
| `filter_dataset-host-path-file.json` | Filtered host paths | Host sorter |
| `filter_dataset-host-file.json` | Filtered host file names | Host sorter |

### Sorted Path JSON

```json
{
  "TRAIN": {
    "csv": ["path/to/file.csv"],
    "pcap": ["path/to/file.pcap"]
  },
  "VALIDATION": {},
  "TEST": {}
}
```

| File | Readers |
|---|---|
| `sort-path-dns-file.json` | DNS content-analysis handlers |
| `sort-path-host-file.json` | Host content-analysis handlers |

### Analysis Summary JSON

Content-analysis summary JSON does not have one shared JSON Schema in code. Common fields used by handlers include:

| Field | Purpose |
|---|---|
| `source_json` | Path to `sort-path-*-file.json`. |
| `role` | TRAIN/VALIDATION/TEST. |
| `format` | Format bucket. |
| `scope` | Counters/paths for analyzed files. |
| `final_status` / `status` | Final analysis status. |
| `blocking_reason` | Reason why analysis cannot proceed, when applicable. |
| detected schema/sample fields | Fields that depend on the concrete analyzer. |

## Stage Two DB/Parquet Contracts

| Layer | DB table | File artifact | Contract source |
|---|---|---|---|
| Raw catalog | `dataset_files` | raw source files | scanner + ingestion metadata |
| Parser execution | `parser_runs` | none | parser registry + parse result counters |
| Normalized | `normalized_artifacts` | normalized Parquet | `schemas/normalized/normalized_event_v1.json` |
| Features | `feature_artifacts` | feature Parquet | `schemas/features/feature_artifact_v1.json` |
| Preprocessing | `preprocessing_artifacts` | fitted preprocessing artifact | registry metadata |
| Model-ready | `model_ready_artifacts` | model-ready Parquet/artifact | `schemas/model_ready/model_ready_v1.json` |

## Normalized Event Concept

Parser output is represented by Stage Two parser contracts and must contain enough metadata to preserve traceability:

| Field group | Purpose |
|---|---|
| source identity | raw file ID/path, parser run linkage, source event UID refs where applicable. |
| split metadata | branch and role. |
| event metadata | event type, timestamp fields when available, labels. |
| raw fields | compact raw fields in JSON metadata for audit/debug. |
| parser metadata | parser name/version/config and schema version. |

The exact column list is defined by `schemas/normalized/normalized_event_v1.json` and registered in `schema_versions` by Stage Two seed.

## Interaction Between Required Components

| Components | Interaction |
|---|---|
| `analyze_dataset` -> `filter_dataset` | Host only: filter reads `host-path-file.json` and `host-file.json`. DNS skips filter. |
| `filter_dataset` -> `sort` | Host sorter requires filtered JSON. DNS sorter reads original DNS discovery JSON. |
| `sort` -> `save_sort` | `save_sort` scans the sorted directory tree created by sorter. |
| `save_sort` -> `dns_analyze` | DNS analyzers read `sort-path-dns-file.json`. |
| `save_sort` -> `host_analyze` | Host analyzers read `sort-path-host-file.json`. |
| Stage One -> Stage Two | Stage Two does not consume Stage One temp JSON directly. It scans configured filesystem roots through `catalog-ingest`. |
