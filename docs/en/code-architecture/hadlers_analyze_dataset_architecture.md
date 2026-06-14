# Handler: `analyze_dataset`

## Purpose

`analyze_dataset` performs the initial scan of DNS and host dataset source directories and creates temporary JSON file lists. It is the first step of the Stage One pipeline.

## CLI

| Command | Class | Input root | Output JSON |
|---|---|---|---|
| `python manage.py handlers analyze-dataset dns-dataset-handler` | `DNSDatasetHandler` | `PATH_DNS_DATASETS` | `dns-path-file.json`, `dns-file.json` |
| `python manage.py handlers analyze-dataset host-dataset-handler` | `HostDatasetHandler` | `PATH_HOST_DATASETS` | `host-path-file.json`, `host-file.json` |

## Components

| File | Purpose |
|---|---|
| `scripts/handlers/analyze_dataset/router_analyze.py` | Routes action to the DNS/host handler. |
| `scripts/handlers/analyze_dataset/dns_dataset_handler.py` | Scans the DNS source root. |
| `scripts/handlers/analyze_dataset/host_dataset_handler.py` | Scans the host source root. |

## Output JSON Contract

Both handlers create two files in `PATH_TEMP_DATA`:

```json
{
  "TRAIN": ["absolute/or/configured/path/to/file"],
  "VALIDATION": ["absolute/or/configured/path/to/file"],
  "TEST": ["absolute/or/configured/path/to/file"]
}
```

`*-path-file.json` stores paths, while `*-file.json` stores file names. Role values must be lists; downstream steps validate this contract explicitly.

## Pipeline Position

```text
analyze_dataset DNS -> sort DNS -> save_sort DNS -> dns_analyze
analyze_dataset host -> filter_dataset host -> sort host -> save_sort host -> host_analyze
```

DNS has no filter step. Host sorting requires the filter step because `sort-host-dataset-handler` reads `filter_dataset-host-*.json`, not the original `host-*.json`.

## Constraints

- The handler does not inspect file contents; it builds a filesystem inventory.
- Roles depend on the current handler logic and source-root layout; a different dataset layout can produce empty role lists.
- The JSON files are temporary Stage One artifacts and are not automatically registered in the PostgreSQL Catalog.
