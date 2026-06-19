# Handler: `sort`

## Purpose

`sort` copies files from temporary JSON lists into a prepared role/format tree. It is the bridge between Stage One discovery/filtering and content analysis.

## CLI

| Command | Class | Input | Output root | Summary |
|---|---|---|---|---|
| `python manage.py handlers sort sort-dns-dataset-handler` | `DNSDatasetSortHandler` | `dns-path-file.json`, `dns-file.json` | `PATH_DNS_DATASETS_FILTER` | `sort-dns-format-summary.json` |
| `python manage.py handlers sort sort-host-dataset-handler` | `HostDatasetSortHandler` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json` | `PATH_HOST_DATASETS_FILTER` | `sort-host-format-summary.json` |

## Components

| File | Purpose |
|---|---|
| `scripts/handlers/sort/router_sort.py` | Routes DNS/host sort actions. |
| `scripts/handlers/sort/sort_dns_dataset_handler.py` | Sorts DNS files. |
| `scripts/handlers/sort/sort_host_dataset_handler.py` | Sorts host files. |

## Output Structure

Sorters create a tree like:

```text
<filter-root>/
  TRAIN/
    csv/
    pcap/
    ...
  VALIDATION/
    ...
  TEST/
    ...
```

Exact format buckets are inferred by sorter logic from file names/extensions. The summary JSON contains counters by role and format plus the output root.

## JSON Summary Contract

The actual summary is built by the handler code and includes:

| Field | Purpose |
|---|---|
| `source_path_json` / input path metadata | Which temporary JSON paths were read. |
| `output_root` | Sorted tree root. |
| `roles` / counters | Processed/copied file counts by role and format. |
| error/skipped counters | Skipped-file information when produced by the handler. |

## Pipeline Position

DNS:

```text
analyze_dataset -> sort-dns-dataset-handler -> save-sort-dns-dataset-handler -> dns_analyze
```

Host:

```text
analyze_dataset -> filter_dataset -> sort-host-dataset-handler -> save-sort-host-dataset-handler -> host_analyze
```

## Constraints

- Sorters operate on the filesystem and may copy large data volumes.
- They do not register files in the PostgreSQL Catalog; Stage Two `catalog-ingest` scans `PATH_FOLDER_DATASETS_FILTER` separately.
- Downstream analysis depends on format bucket names matching action-specific handlers.
