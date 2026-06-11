# Handlers Architecture: analyze_dataset

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Package Files](#2-package-files)
- [3. Service Startup](#3-service-startup)
- [4. Call Chain](#4-call-chain)
- [5. Router Functions](#5-router-functions)
- [6. DNSDatasetHandler](#6-dnsdatasethandler)
- [7. HostDatasetHandler](#7-hostdatasethandler)
- [8. Output JSON Artifacts](#8-output-json-artifacts)
- [9. Errors and Limitations](#9-errors-and-limitations)

## 1. Purpose

`scripts/handlers/analyze_dataset` performs the first pipeline stage: it recursively scans source DNS/Host directories, detects file roles, and writes intermediate JSON files with file paths and file names.

This service does not inspect file contents. Its job is to build a file index used by later stages: `filter_dataset`, `sort`, `save_sort`, `dns_analyze`, and `host_analyze`.

## 2. Package Files

| File | Purpose |
|---|---|
| `router_analyze.py` | Routes actions inside the `analyze-dataset` service. |
| `dns_dataset_handler.py` | Scans DNS datasets and writes `dns-path-file.json`, `dns-file.json`. |
| `host_dataset_handler.py` | Scans Host datasets and writes `host-path-file.json`, `host-file.json`. |
| `__init__.py` | Package marker, no public classes are exported. |

## 3. Service Startup

Commands:

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers analyze-dataset host-dataset-handler
```

`manage.py` receives:

```text
module=handlers
service=analyze-dataset
action=dns-dataset-handler | host-dataset-handler
```

Then the command flows through:

```text
manage.manage()
-> router_commands()
-> router_commands_handlers()
-> router_analyze()
```

## 4. Call Chain

DNS:

```text
python manage.py handlers analyze-dataset dns-dataset-handler
-> manage.manage()
-> scripts.router_script.router_commands("handlers", "analyze-dataset", "dns-dataset-handler")
-> scripts.handlers.router_handler.router_commands_handlers("analyze-dataset", "dns-dataset-handler")
-> scripts.handlers.analyze_dataset.router_analyze.router_analyze("dns-dataset-handler")
-> dns_dataset_handler()
-> DNSDatasetHandler(PATH_DNS_DATASETS, PATH_TEMP_DATA)
-> DNSDatasetHandler.analyze_and_save()
-> JsonDataManager(...).write(...)
```

Host:

```text
python manage.py handlers analyze-dataset host-dataset-handler
-> manage.manage()
-> router_commands(...)
-> router_commands_handlers(...)
-> router_analyze("host-dataset-handler")
-> host_dataset_handler()
-> HostDatasetHandler(PATH_HOST_DATASETS, PATH_TEMP_DATA)
-> HostDatasetHandler.analyze_and_save()
-> JsonDataManager(...).write(...)
```

## 5. Router Functions

### `router_analyze(action: str)`

Selects the handler by `action`.

| Action | Called function |
|---|---|
| `dns-dataset-handler` | `dns_dataset_handler()` |
| `host-dataset-handler` | `host_dataset_handler()` |
| any other value | prints `manage_commands` |

### `dns_dataset_handler()`

Creates `DNSDatasetHandler` with paths from `config.py`:

- `PATH_DNS_DATASETS`;
- `PATH_TEMP_DATA`.

After execution it prints:

- path JSON file;
- file-name JSON file.

### `host_dataset_handler()`

Creates `HostDatasetHandler` with paths from `config.py`:

- `PATH_HOST_DATASETS`;
- `PATH_TEMP_DATA`.

After execution it prints the equivalent Host result.

## 6. DNSDatasetHandler

File:

- `scripts/handlers/analyze_dataset/dns_dataset_handler.py`

### Classes

| Class | Purpose |
|---|---|
| `DNSAnalysisResult` | Immutable result dataclass: JSON paths and grouped data. |
| `DNSDatasetHandler` | Main DNS dataset scanning handler. |

### Roles

`DNSDatasetHandler.ROLE_KEYWORDS`:

| Role | Path tokens |
|---|---|
| `TRAIN` | `train`, `training` |
| `TEST` | `test`, `testing` |
| `VALIDATION` | `validation`, `valid`, `val`, `dev`, `eval` |
| `EXPERIMENTS` | `experiment`, `experiments`, `exp`, `sandbox`, `trial` |

If no role is detected, `EXPERIMENTS` is used.

### Main Method

`analyze_and_save()`:

1. Calls `_validate_dns_root_path()`.
2. Creates empty role sets through `_init_role_sets()`.
3. Reads directories with files through `_walk_dns_files()`.
4. Detects each directory role with `_detect_role(path)`.
5. Adds each full file path to `paths_by_role_set`.
6. Adds each file name to `files_by_role_set`.
7. Converts sets to sorted lists through `_prepare_output()`.
8. Writes `dns-path-file.json`.
9. Writes `dns-file.json`.
10. Returns `DNSAnalysisResult`.

### Helper Methods

| Method | Logic |
|---|---|
| `_validate_dns_root_path()` | Ensures `PATH_DNS_DATASETS` is configured, exists, and is a directory. |
| `_walk_dns_files()` | Recursively scans `dns_datasets_path.rglob("*")` and groups files by directory. |
| `_detect_role(path)` | Tokenizes the path and searches role keywords. |
| `_tokenize(value)` | Splits a string with regex `[^a-z0-9]+`. |
| `_init_role_sets()` | Creates `{role: set()}` for all DNS roles. |
| `_prepare_output(role_map)` | Returns `{role: sorted(list)}`. |

## 7. HostDatasetHandler

File:

- `scripts/handlers/analyze_dataset/host_dataset_handler.py`

### Classes

| Class | Purpose |
|---|---|
| `HostAnalysisResult` | Immutable result dataclass: JSON paths and grouped data. |
| `HostDatasetHandler` | Main Host dataset scanning handler. |

### Roles

`HostDatasetHandler.ROLE_KEYWORDS`:

| Role | Path tokens |
|---|---|
| `TRAIN` | `train`, `training` |
| `TEST` | `test`, `testing` |
| `VALIDATION` | `validation`, `valid`, `val`, `dev`, `eval` |

If no role is detected, `TEST` is used.

### Main Method

`analyze_and_save()` mirrors the DNS version, but writes Host artifacts:

- `host-path-file.json`;
- `host-file.json`.

### Helper Methods

| Method | Logic |
|---|---|
| `_validate_host_root_path()` | Ensures `PATH_HOST_DATASETS` is configured, exists, and is a directory. |
| `_walk_host_files()` | Recursively groups found files by directory. |
| `_detect_role(path)` | Detects role from path tokens. |
| `_tokenize(value)` | Normalizes a path string into tokens. |
| `_init_role_sets()` | Creates `{role: set()}` for Host roles. |
| `_prepare_output(role_map)` | Converts sets into sorted lists for JSON. |

## 8. Output JSON Artifacts

DNS:

```text
PATH_TEMP_DATA/dns-path-file.json
PATH_TEMP_DATA/dns-file.json
```

Host:

```text
PATH_TEMP_DATA/host-path-file.json
PATH_TEMP_DATA/host-file.json
```

Data shape:

```json
{
  "TRAIN": ["/absolute/path/to/file"],
  "TEST": [],
  "VALIDATION": []
}
```

For `*-file.json`, only file basenames are stored instead of full paths.

## 9. Errors and Limitations

- Handlers validate paths and names, not file contents.
- Role detection is path-token based, so classification quality depends on directory naming.
- DNS supports `EXPERIMENTS`; Host does not.
- Unrecognized Host files are assigned to `TEST`, which can be surprising for new datasets.
- Later stages depend on fresh JSON files in `PATH_TEMP_DATA`.
