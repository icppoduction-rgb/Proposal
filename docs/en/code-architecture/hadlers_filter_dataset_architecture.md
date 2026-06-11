# Handlers Architecture: filter_dataset

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Package Files](#2-package-files)
- [3. Service Startup](#3-service-startup)
- [4. Call Chain](#4-call-chain)
- [5. Router Functions](#5-router-functions)
- [6. HostDatasetFilterHandler](#6-hostdatasetfilterhandler)
- [7. Filtering Rules](#7-filtering-rules)
- [8. Output Artifacts](#8-output-artifacts)
- [9. Errors and Limitations](#9-errors-and-limitations)

## 1. Purpose

`scripts/handlers/filter_dataset` filters Host datasets after the initial scan. The service keeps only files matching the expected role, dataset name, and allowed file extension rules.

DNS files do not pass through this service.

## 2. Package Files

| File | Purpose |
|---|---|
| `router_filter.py` | Routes the `filter-host-dataset-handler` action. |
| `filter_host_dataset_handler.py` | Contains `HostDatasetFilterHandler` and `HostFilterResult`. |
| `__init__.py` | Package marker. |

## 3. Service Startup

```bash
python manage.py handlers filter-dataset filter-host-dataset-handler
```

Before running, these files must exist:

```text
PATH_TEMP_DATA/host-path-file.json
PATH_TEMP_DATA/host-file.json
```

They are created by:

```bash
python manage.py handlers analyze-dataset host-dataset-handler
```

## 4. Call Chain

```text
python manage.py handlers filter-dataset filter-host-dataset-handler
-> manage.manage()
-> router_commands("handlers", "filter-dataset", "filter-host-dataset-handler")
-> router_commands_handlers("filter-dataset", "filter-host-dataset-handler")
-> router_filter("filter-host-dataset-handler")
-> filter_host_dataset_handler()
-> HostDatasetFilterHandler(PATH_TEMP_DATA, PATH_FILTER_LOG)
-> HostDatasetFilterHandler.filter_and_save()
-> JsonDataManager(...).read(...)
-> HostDatasetFilterHandler._is_allowed_file(...)
-> JsonDataManager(...).write(...)
```

## 5. Router Functions

### `router_filter(action: str)`

| Action | Called function |
|---|---|
| `filter-host-dataset-handler` | `filter_host_dataset_handler()` |
| any other value | prints `manage_commands` |

### `filter_host_dataset_handler()`

Creates `HostDatasetFilterHandler` with:

- `temp_data_path=PATH_TEMP_DATA`;
- `log_file_path=PATH_FILTER_LOG`.

After execution it prints:

- output JSON paths;
- log path;
- kept and excluded file counts;
- exclusion reasons.

## 6. HostDatasetFilterHandler

File:

- `scripts/handlers/filter_dataset/filter_host_dataset_handler.py`

### Classes

| Class | Purpose |
|---|---|
| `HostFilterResult` | Filtering result dataclass. |
| `HostDatasetFilterHandler` | Main Host file filtering handler. |

### Main Method

`filter_and_save()`:

1. Reads `host-path-file.json`.
2. Reads `host-file.json`.
3. Validates required roles through `_validate_source_json()`.
4. Normalizes file names by role through `_normalize_files_by_role()`.
5. Checks the type of each path value.
6. Extracts the dataset name through `_extract_dataset_name()`.
7. Checks whether the dataset is allowed for the role.
8. Checks the file through `_is_allowed_file()`.
9. Ensures the basename exists in `host-file.json`.
10. Stores valid paths and names in set structures.
11. Writes `filter_dataset-host-path-file.json`.
12. Writes `filter_dataset-host-file.json`.
13. Returns `HostFilterResult`.

### Helper Methods

| Method | Logic |
|---|---|
| `_build_logger()` | Creates a logger and file handler for excluded files. |
| `_track_exclusion(...)` | Increments reason count and writes a log line. |
| `_validate_source_json(...)` | Ensures `TRAIN`, `TEST`, `VALIDATION` exist. |
| `_normalize_files_by_role(...)` | Converts file names to sets by role. |
| `_is_allowed_file(...)` | Applies dataset and extension allowlist rules. |
| `_extract_dataset_name(file_path)` | Extracts dataset name from the path after the `host` segment. |
| `_normalize_path_text(file_path)` | Normalizes path separators to `/`. |
| `_path_name(file_path)` | Returns basename for POSIX/Windows paths. |
| `_init_role_sets()` | Creates empty role set structures. |
| `_prepare_output(...)` | Converts sets into sorted lists. |

## 7. Filtering Rules

### Roles and Datasets

| Role | Allowed datasets |
|---|---|
| `TRAIN` | `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset` |
| `TEST` | `Unified-Host-Network-Dataset -LANL`, `ISOT-Cloud-IDS-Dataset`, `Dynamic-Malware-Analysis-Dataset` |
| `VALIDATION` | `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets` |

### Extensions

| Dataset | Allowed extensions / rules |
|---|---|
| `ADFA IDS` | `.txt`, `.ghc`, `.csv`, `.netflow_ids`, `.xml` |
| `LID-DS 2021` | `.sc`, `.json` |
| `LID-DS 2019` | `.txt`, `.csv` |
| `Windows-Event-Log -OTRF-Security-Datasets` | `.json`, `.cap`, `.pcap`, `.pcapng` |
| `ISOT-Cloud-IDS-Dataset` | `.csv` |
| `Dynamic-Malware-Analysis-Dataset` | `.txt`, `.json`, `.bson`, `.log` |
| `Maintainable Log Dataset` | Only paths containing `/logs/`, `/alerts_csv/`, `/labels/`, excluding binary/office extensions. |
| `LANL Dataset` | All files are allowed. |
| `Unified-Host-Network-Dataset -LANL` | All files are allowed. |

## 8. Output Artifacts

```text
PATH_TEMP_DATA/filter_dataset-host-path-file.json
PATH_TEMP_DATA/filter_dataset-host-file.json
PATH_FILTER_LOG
```

`HostFilterResult` also returns:

- `kept_files_count`;
- `excluded_files_count`;
- `excluded_by_reason`;
- grouped file paths and names.

## 9. Errors and Limitations

- Filtering depends on path structure: dataset name is extracted after the `host` segment.
- If a path does not match the expected structure, the file is excluded with `dataset_name_not_detected`.
- The logger clears previous handlers to avoid duplicate lines and writes in `w` mode.
- `PATH_FILTER_LOG` must be a string or compatible path-like value.
- New datasets must be explicitly added to `DATASET_ROLE_MAP` and `_is_allowed_file()`.
