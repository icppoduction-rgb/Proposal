# Handlers Architecture: save_sort

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Package Files](#2-package-files)
- [3. Service Startup](#3-service-startup)
- [4. Call Chain](#4-call-chain)
- [5. Router Functions](#5-router-functions)
- [6. DNSSortedPathExportHandler](#6-dnssortedpathexporthandler)
- [7. HostSortedPathExportHandler](#7-hostsortedpathexporthandler)
- [8. Output JSON Artifacts](#8-output-json-artifacts)
- [9. Errors and Limitations](#9-errors-and-limitations)

## 1. Purpose

`scripts/handlers/save_sort` scans the already sorted dataset tree and writes JSON files with paths grouped by role and format.

This service does not copy or move files. It only reads `PATH_*_DATASETS_FILTER` and creates an index for content-analysis handlers.

## 2. Package Files

| File | Purpose |
|---|---|
| `router_save.py` | Routes `save-sort-host-dataset-handler` and `save-sort-dns-dataset-handler`. |
| `save_sort_dns_path_handler.py` | Exports DNS file paths. |
| `save_sort_host_path_handler.py` | Exports Host file paths. |
| `__init__.py` | Package marker. |

## 3. Service Startup

DNS:

```bash
python manage.py handlers save-sort save-sort-dns-dataset-handler
```

Host:

```bash
python manage.py handlers save-sort save-sort-host-dataset-handler
```

Before running, `sort` must have created `PATH_DNS_DATASETS_FILTER` or `PATH_HOST_DATASETS_FILTER`.

## 4. Call Chain

DNS:

```text
python manage.py handlers save-sort save-sort-dns-dataset-handler
-> router_commands(...)
-> router_commands_handlers("save-sort", "save-sort-dns-dataset-handler")
-> router_save("save-sort-dns-dataset-handler")
-> save_sort_dns_dataset_handler()
-> DNSSortedPathExportHandler(PATH_DNS_DATASETS_FILTER, PATH_TEMP_DATA)
-> export_paths()
-> _validate_source_root()
-> _scan_role_directory(...)
-> JsonDataManager(sort-path-dns-file.json).write(...)
```

Host:

```text
python manage.py handlers save-sort save-sort-host-dataset-handler
-> router_save("save-sort-host-dataset-handler")
-> save_sort_host_dataset_handler()
-> HostSortedPathExportHandler(PATH_HOST_DATASETS_FILTER, PATH_TEMP_DATA)
-> export_paths()
-> _scan_role_directory(...)
-> JsonDataManager(sort-path-host-file.json).write(...)
```

## 5. Router Functions

### `router_save(action: str)`

| Action | Called function |
|---|---|
| `save-sort-host-dataset-handler` | `save_sort_host_dataset_handler()` |
| `save-sort-dns-dataset-handler` | `save_sort_dns_dataset_handler()` |
| any other value | prints `manage_commands` |

## 6. DNSSortedPathExportHandler

File:

- `scripts/handlers/save_sort/save_sort_dns_path_handler.py`

### Classes

| Class | Purpose |
|---|---|
| `DNSSortedPathExportResult` | DNS path export result dataclass. |
| `DNSSortedPathExportHandler` | Scans `PATH_DNS_DATASETS_FILTER`. |

### Roles

```text
TRAIN, TEST, VALIDATION, EXPERIMENTS
```

### Main Method

`export_paths()`:

1. Validates source root through `_validate_source_root()`.
2. Creates `{role: {}}`.
3. For each role, checks `PATH_DNS_DATASETS_FILTER/<ROLE>`.
4. Scans format directories through `_scan_role_directory()`.
5. Counts files.
6. Writes `sort-path-dns-file.json`.
7. Writes `sort-path-dns-file-summary.json`.
8. Returns `DNSSortedPathExportResult`.

## 7. HostSortedPathExportHandler

File:

- `scripts/handlers/save_sort/save_sort_host_path_handler.py`

### Classes

| Class | Purpose |
|---|---|
| `HostSortedPathExportResult` | Host path export result dataclass. |
| `HostSortedPathExportHandler` | Scans `PATH_HOST_DATASETS_FILTER`. |

### Roles

```text
TRAIN, TEST, VALIDATION
```

### Main Method

`export_paths()` mirrors DNS logic, but works with the Host root and writes Host JSON.

### `_scan_role_directory(role_directory)`

Common algorithm:

1. Iterates over child directories of the role.
2. Each child directory is treated as `format`.
3. Recursively collects all files with `format_directory.rglob("*")`.
4. Stores absolute paths through `path.resolve()`.
5. Returns `{format_name: [paths]}` only for non-empty format directories.

## 8. Output JSON Artifacts

DNS:

```text
PATH_TEMP_DATA/sort-path-dns-file.json
PATH_TEMP_DATA/sort-path-dns-file-summary.json
```

Host:

```text
PATH_TEMP_DATA/sort-path-host-file.json
PATH_TEMP_DATA/sort-path-host-file-summary.json
```

Main JSON shape:

```json
{
  "TRAIN": {
    "csv": ["/absolute/path/file.csv"]
  },
  "TEST": {},
  "VALIDATION": {}
}
```

Summary contains:

- `json_file`;
- `scanned_files_count`;
- `counts_by_role_and_format`.

## 9. Errors and Limitations

- Missing root path raises `ValueError`.
- Non-existing root path raises `FileNotFoundError`.
- Non-directory root path raises `NotADirectoryError`.
- Empty format directories are omitted from the output JSON.
- The service does not validate file contents; it indexes paths only.
