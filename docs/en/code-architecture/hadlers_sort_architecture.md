# Handlers Architecture: sort

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Package Files](#2-package-files)
- [3. Service Startup](#3-service-startup)
- [4. Call Chain](#4-call-chain)
- [5. Router Functions](#5-router-functions)
- [6. DNSDatasetSortHandler](#6-dnsdatasetsorthandler)
- [7. HostDatasetSortHandler](#7-hostdatasetsorthandler)
- [8. File Materialization Logic](#8-file-materialization-logic)
- [9. Output Artifacts](#9-output-artifacts)
- [10. Errors and Limitations](#10-errors-and-limitations)

## 1. Purpose

`scripts/handlers/sort` sorts discovered files by role and format. The service creates a physical directory tree:

```text
PATH_*_DATASETS_FILTER/
└── <ROLE>/
    └── <format>/
        └── <file>
```

DNS sorting uses `dns-path-file.json` and `dns-file.json`. Host sorting uses filtered files from `filter_dataset-host-path-file.json` and `filter_dataset-host-file.json`.

## 2. Package Files

| File | Purpose |
|---|---|
| `router_sort.py` | Routes `sort-host-dataset-handler` and `sort-dns-dataset-handler`. |
| `sort_dns_dataset_handler.py` | Sorts DNS files by role and format group. |
| `sort_host_dataset_handler.py` | Sorts Host files by role and format group. |
| `__init__.py` | Package marker. |

## 3. Service Startup

DNS:

```bash
python manage.py handlers sort sort-dns-dataset-handler
```

Host:

```bash
python manage.py handlers sort sort-host-dataset-handler
```

Before the DNS route runs, these files must exist:

```text
PATH_TEMP_DATA/dns-path-file.json
PATH_TEMP_DATA/dns-file.json
```

Before the Host route runs, these files must exist:

```text
PATH_TEMP_DATA/filter_dataset-host-path-file.json
PATH_TEMP_DATA/filter_dataset-host-file.json
```

## 4. Call Chain

DNS:

```text
python manage.py handlers sort sort-dns-dataset-handler
-> manage.manage()
-> router_commands(...)
-> router_commands_handlers("sort", "sort-dns-dataset-handler")
-> router_sort("sort-dns-dataset-handler")
-> sort_dns_dataset_handler()
-> DNSDatasetSortHandler(PATH_TEMP_DATA, PATH_DNS_DATASETS_FILTER)
-> sort_and_prepare()
-> _validate_output_root()
-> JsonDataManager(...).read(...)
-> _detect_format_group(...)
-> _build_destination_path(...)
-> _materialize_file(...)
-> JsonDataManager(sort-dns-format-summary.json).write(...)
```

Host:

```text
python manage.py handlers sort sort-host-dataset-handler
-> router_sort("sort-host-dataset-handler")
-> sort_host_dataset_handler()
-> HostDatasetSortHandler(PATH_TEMP_DATA, PATH_HOST_DATASETS_FILTER)
-> sort_and_prepare()
-> _detect_format_group(...)
-> _materialize_file(...)
-> JsonDataManager(sort-host-format-summary.json).write(...)
```

## 5. Router Functions

### `router_sort(action: str)`

| Action | Called function |
|---|---|
| `sort-host-dataset-handler` | `sort_host_dataset_handler()` |
| `sort-dns-dataset-handler` | `sort_dns_dataset_handler()` |
| any other value | prints `manage_commands` |

### `sort_host_dataset_handler()`

Creates `HostDatasetSortHandler` with:

- `temp_data_path=PATH_TEMP_DATA`;
- `host_datasets_filter_path=PATH_HOST_DATASETS_FILTER`.

### `sort_dns_dataset_handler()`

Creates `DNSDatasetSortHandler` with:

- `temp_data_path=PATH_TEMP_DATA`;
- `dns_datasets_filter_path=PATH_DNS_DATASETS_FILTER`.

## 6. DNSDatasetSortHandler

File:

- `scripts/handlers/sort/sort_dns_dataset_handler.py`

### Classes

| Class | Purpose |
|---|---|
| `DNSDatasetSortResult` | DNS sorting result dataclass. |
| `DNSDatasetSortHandler` | Main DNS sort handler. |

### Roles

```text
TRAIN, TEST, VALIDATION, EXPERIMENTS
```

### Main Method

`sort_and_prepare()`:

1. Validates the target directory through `_validate_output_root()`.
2. Reads `dns-path-file.json`.
3. Reads `dns-file.json`.
4. Validates required roles through `_validate_source_json()`.
5. Normalizes file names through `_normalize_file_names()`.
6. Normalizes paths through `_normalize_file_paths()`.
7. Creates base role directories through `_create_base_role_directories()`.
8. Detects file format through `_detect_format_group()`.
9. Creates the `<ROLE>/<format>` directory.
10. Resolves destination through `_build_destination_path()`.
11. Creates a hardlink or copy through `_materialize_file()`.
12. Writes `sort-dns-format-summary.json`.
13. Returns `DNSDatasetSortResult`.

### DNS Format Detection

`_detect_format_group(file_name)`:

| Condition | Format group |
|---|---|
| ends with `.pcap.csv` | `pcap.csv` |
| ends with `.pcap` | `pcap` |
| ends with `.csv` | `csv` |
| ends with `.txt` | `txt` |
| has another extension | suffix without dot |
| no extension | file name |

## 7. HostDatasetSortHandler

File:

- `scripts/handlers/sort/sort_host_dataset_handler.py`

### Classes

| Class | Purpose |
|---|---|
| `HostDatasetSortResult` | Host sorting result dataclass. |
| `HostDatasetSortHandler` | Main Host sort handler. |

### Roles

```text
TRAIN, TEST, VALIDATION
```

### Main Method

`sort_and_prepare()` follows the same sorting logic as DNS, but reads:

- `filter_dataset-host-path-file.json`;
- `filter_dataset-host-file.json`.

### Host Format Detection

`_detect_format_group(file_name)` has special Host file-name rules:

| Condition | Format group |
|---|---|
| `netflow_day-\d+` | `netflow_day` |
| `wls_day-\d+` | `wls_day` |
| ends with `journal~` | `journal~` |
| `messages` | `messages` |
| `messages.<n>` | `messages-<n>` |
| `mainlog.<n>` | `mainlog-<n>` |
| `log.<n>` | `log-<n>` |
| `*.pcap.<timestamp>` | `pcap` |
| `info.<n>` | `info-<n>` |
| semantic logs: `auth.log`, `cpu.log`, `diskio.log`, ... | matching semantic format |
| rotated `.log`, `.json`, `syslog` | `log-<n>`, `json-<n>`, `syslog-<n>` |
| `.netflow_ids` | `netflow_ids` |
| another extension | suffix without dot |
| no extension | file name |

## 8. File Materialization Logic

Both sort handlers use the same algorithm:

```text
source_path
-> _build_destination_path(role_dir, source_path)
-> if destination exists and samefile: skip
-> else _materialize_file(source_path, destination_path)
```

`_materialize_file()`:

1. If destination already exists and points to source, returns `True`.
2. If destination exists but is a different file, raises `FileExistsError`.
3. Tries to create a hardlink with `os.link(source_path, destination_path)`.
4. If `os.link` raises `OSError`, copies with `shutil.copy2(...)`.
5. Returns `True` for hardlink, `False` for copy.

Name collisions are resolved through `_destination_name_with_hash()`, where the hash is built from the full source path.

## 9. Output Artifacts

DNS:

```text
PATH_DNS_DATASETS_FILTER/<ROLE>/<format>/*
PATH_TEMP_DATA/sort-dns-format-summary.json
```

Host:

```text
PATH_HOST_DATASETS_FILTER/<ROLE>/<format>/*
PATH_TEMP_DATA/sort-host-format-summary.json
```

Summary includes:

- `sorted_root_path`;
- `created_links_count`;
- `copied_files_count`;
- `skipped_existing_count`;
- `missing_source_count`;
- `name_mismatch_count`;
- `files_by_role_and_format`.

## 10. Errors and Limitations

- Sort stage depends on fresh input JSON.
- Host sort expects `filter_dataset` output, not raw `host-path-file.json`.
- Missing required roles raise `ValueError`.
- Missing source files increment `missing_source_count` and are skipped.
- Hardlinks may not work across different file systems; copy fallback is implemented.
- New Host formats may require updating `_detect_format_group()`.
