# Handler: `save_sort`

## Purpose

`save_sort` scans an already sorted `PATH_*_DATASETS_FILTER` tree and creates a JSON path map consumed by `dns_analyze` and `host_analyze`.

## CLI

| Command | Class | Input root | Output JSON |
|---|---|---|---|
| `python manage.py handlers save-sort save-sort-dns-dataset-handler` | `DNSSortedPathExportHandler` | `PATH_DNS_DATASETS_FILTER` | `sort-path-dns-file.json`, `sort-path-dns-file-summary.json` |
| `python manage.py handlers save-sort save-sort-host-dataset-handler` | `HostSortedPathExportHandler` | `PATH_HOST_DATASETS_FILTER` | `sort-path-host-file.json`, `sort-path-host-file-summary.json` |

## Components

| File | Purpose |
|---|---|
| `scripts/handlers/save_sort/router_save.py` | Routes DNS/host save-sort actions. |
| `scripts/handlers/save_sort/save_sort_dns_path_handler.py` | Exports DNS sorted paths. |
| `scripts/handlers/save_sort/save_sort_host_path_handler.py` | Exports host sorted paths. |

## `sort-path-*-file.json` Contract

The file represents a role/format tree:

```json
{
  "TRAIN": {
    "csv": ["path/to/file.csv"],
    "pcap": ["path/to/file.pcap"]
  },
  "VALIDATION": {
    "txt": ["path/to/file.txt"]
  },
  "TEST": {
    "json": ["path/to/file.json"]
  }
}
```

Content-analysis handlers read this JSON and select the role/format bucket matching the action.

## Pipeline Position

```text
sort -> save_sort -> dns_analyze / host_analyze
```

`dns_analyze` reads `sort-path-dns-file.json`. `host_analyze` reads `sort-path-host-file.json`.

## Constraints

- `save_sort` does not inspect file contents.
- If the sorted tree is empty or a bucket is missing, downstream content-analysis handlers usually create a blocking summary or raise an error, depending on the concrete implementation.
- JSON path export does not replace Stage Two catalog ingestion; the PostgreSQL Catalog is populated by `stage-two catalog-ingest`.
