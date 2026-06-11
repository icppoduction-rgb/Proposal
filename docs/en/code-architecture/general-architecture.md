# General Code Architecture

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. CLI Entry Point](#2-cli-entry-point)
- [3. Routing Model](#3-routing-model)
- [4. Main Code Layers](#4-main-code-layers)
- [5. Dataset Processing Pipeline](#5-dataset-processing-pipeline)
- [6. JSON Artifacts and Documentation](#6-json-artifacts-and-documentation)
- [7. Management Commands](#7-management-commands)
- [8. Adding a New Handler](#8-adding-a-new-handler)
- [9. Technical Constraints and Risks](#9-technical-constraints-and-risks)
- [10. Improvement Recommendations](#10-improvement-recommendations)

## 1. Purpose

The code in `manage.py` and `scripts/*` implements a CLI tool for preparing, sorting, and analyzing DNS/Host datasets. Its main responsibilities are:

- scan source dataset directories;
- group files by role: `TRAIN`, `TEST`, `VALIDATION`, and, for DNS, `EXPERIMENTS`;
- filter Host files by allowed dataset and extension rules;
- sort files by detected format;
- persist intermediate JSON artifacts;
- generate markdown documentation and reports for dataset file contents.

The code is designed for batch execution from the command line. State is passed between pipeline stages through JSON files stored in `PATH_TEMP_DATA`.

## 2. CLI Entry Point

The main entry point is `manage.py`.

`manage.py`:

- creates an `argparse.ArgumentParser`;
- accepts three positional arguments:
  - `module`;
  - `service`;
  - `action`;
- calls `scripts.router_script.router_commands(module, service, action)`.

General command shape:

```bash
python manage.py handlers <service> <action>
```

If `module` is not `handlers`, the CLI prints `manage_commands` from `config.py`.

## 3. Routing Model

Routing is implemented as a simple function tree.

```text
manage.py
└── scripts/router_script.py
    └── scripts/handlers/router_handler.py
        ├── analyze-dataset  -> scripts/handlers/analyze_dataset/router_analyze.py
        ├── filter-dataset   -> scripts/handlers/filter_dataset/router_filter.py
        ├── sort             -> scripts/handlers/sort/router_sort.py
        ├── save-sort        -> scripts/handlers/save_sort/router_save.py
        ├── dns-analyze      -> scripts/handlers/dns_analyze/router_dns.py
        └── host-analyze     -> scripts/handlers/host_analyze/router_host.py
```

Each router receives a string `action`, compares it with supported action names, and calls the corresponding handler. If the action is unknown, the router prints `manage_commands`.

## 4. Main Code Layers

### 4.1. CLI and Routing

Files:

- `manage.py`;
- `scripts/router_script.py`;
- `scripts/handlers/router_handler.py`;
- `scripts/handlers/*/router_*.py`;
- `scripts/handlers/dns_analyze/run_action.py`;
- `scripts/handlers/host_analyze/run_action.py`.

Layer responsibilities:

- accept a user command;
- select the requested service/action;
- instantiate the handler class;
- pass paths from `config.py`;
- print a short execution result through `rich.console.Console`.

### 4.2. Shared JSON Layer

Files:

- `scripts/handlers/json_handler/json_data.py`;
- `scripts/handlers/json_handler/json-data.py`.

`JsonDataManager` encapsulates JSON file operations:

- create the parent directory before writing;
- check file existence;
- read a JSON object;
- fully overwrite a JSON file;
- update top-level keys.

The `json-data.py` module is a compatibility wrapper that re-exports `JsonDataManager` from `json_data.py`.

### 4.3. Initial Dataset Structure Analysis

Files:

- `scripts/handlers/analyze_dataset/dns_dataset_handler.py`;
- `scripts/handlers/analyze_dataset/host_dataset_handler.py`.

DNS and Host handlers scan source directories, infer the role from path tokens, and write two JSON files:

- `<type>-path-file.json` - full file paths grouped by role;
- `<type>-file.json` - file names grouped by role.

DNS roles:

- `TRAIN`;
- `TEST`;
- `VALIDATION`;
- `EXPERIMENTS`.

Host roles:

- `TRAIN`;
- `TEST`;
- `VALIDATION`.

If a Host role cannot be detected, the file is assigned to `TEST`. If a DNS role cannot be detected, the file is assigned to `EXPERIMENTS`.

### 4.4. Host Dataset Filtering

File:

- `scripts/handlers/filter_dataset/filter_host_dataset_handler.py`.

`HostDatasetFilterHandler` reads:

- `host-path-file.json`;
- `host-file.json`.

Then it applies filtering rules based on dataset name, role, and file extension.

Main checks:

- path value has a valid type;
- dataset name can be extracted from the path;
- dataset is allowed for the detected role;
- file extension is allowed for that dataset;
- file name exists in `host-file.json`.

Filtering outputs:

- `filter_dataset-host-path-file.json`;
- `filter_dataset-host-file.json`;
- log file with excluded files.

### 4.5. Sorting by Role and Format

Files:

- `scripts/handlers/sort/sort_dns_dataset_handler.py`;
- `scripts/handlers/sort/sort_host_dataset_handler.py`.

Sorting reads intermediate JSON files and creates this structure:

```text
PATH_*_DATASETS_FILTER/
└── <ROLE>/
    └── <format>/
        └── <file>
```

File materialization uses:

1. `os.link` - hardlink without duplicating file data;
2. `shutil.copy2` - fallback when hardlink creation is not possible.

When a target name collides, the destination name receives a hash derived from the source path. This reduces the risk of overwriting same-named files from different directories.

### 4.6. Sorted Path Export

Files:

- `scripts/handlers/save_sort/save_sort_dns_path_handler.py`;
- `scripts/handlers/save_sort/save_sort_host_path_handler.py`.

Export scans the already sorted `PATH_*_DATASETS_FILTER` tree and writes JSON shaped like:

```json
{
  "TRAIN": {
    "csv": ["/abs/path/file.csv"]
  },
  "TEST": {},
  "VALIDATION": {}
}
```

Main output files:

- `sort-path-dns-file.json`;
- `sort-path-dns-file-summary.json`;
- `sort-path-host-file.json`;
- `sort-path-host-file-summary.json`.

### 4.7. DNS Content Analysis

Files:

- `scripts/handlers/dns_analyze/*`;
- `scripts/handlers/dns_analyze/router_dns.py`;
- `scripts/handlers/dns_analyze/run_action.py`.

DNS content-analysis handlers read `sort-path-dns-file.json`, select a role/format bucket, analyze sampled files, and generate:

- summary JSON;
- markdown document under `docs/ru/...`;
- markdown document under `docs/en/...`;
- `README.md` for the corresponding documentation directory;
- markdown reports under `report/...`.

Supported analysis targets:

| Role | Formats |
|---|---|
| `TRAIN` | `csv`, `pcap`, `pcap.csv` |
| `TEST` | `csv`, `pcap`, `pcap.csv` |
| `VALIDATION` | `pcap`, `txt` |

### 4.8. Host Content Analysis

Files:

- `scripts/handlers/host_analyze/*`;
- `scripts/handlers/host_analyze/router_host.py`;
- `scripts/handlers/host_analyze/run_action.py`.

Host content-analysis handlers read `sort-path-host-file.json`, analyze a specific `role/format` pair, and generate bilingual documentation.

Supported groups:

- `TRAIN`: `csv`, `auth.log`, `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `ghc`, `info`, `journal`, `journal~`, `json`, `json-1`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `netflow_ids`, `network.log`, `pcap`, `process.log`, `process.summary.log`, `sc`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `txt`, `uptime.log`, `xml`;
- `TEST`: `bson`, `csv`, `json`, `log`, `netflow_day`, `txt`, `wls_day`;
- `VALIDATION`: `cap`, `csv`, `json`, `netflow_day`, `pcap`, `pcapng`, `txt`, `wls_day`.

## 5. Dataset Processing Pipeline

Recommended DNS sequence:

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers dns-analyze <dns-action>
```

Recommended Host sequence:

```bash
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers host-analyze <host-action>
```

Stage dependencies:

| Stage | Input | Output |
|---|---|---|
| `analyze-dataset` | source directories `PATH_HOST_DATASETS` / `PATH_DNS_DATASETS` | `host-path-file.json`, `host-file.json`, `dns-path-file.json`, `dns-file.json` |
| `filter-dataset` | `host-path-file.json`, `host-file.json` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json` |
| `sort` | DNS: `dns-*.json`; Host: `filter_dataset-host-*.json` | sorted directories, `sort-*-format-summary.json` |
| `save-sort` | sorted directories | `sort-path-*-file.json`, `sort-path-*-file-summary.json` |
| `dns-analyze` / `host-analyze` | `sort-path-*-file.json` | summary JSON, docs, reports |

## 6. JSON Artifacts and Documentation

### 6.1. Temporary JSON Files

All intermediate JSON files are stored in `PATH_TEMP_DATA`.

Key files:

- `dns-path-file.json`;
- `dns-file.json`;
- `host-path-file.json`;
- `host-file.json`;
- `filter_dataset-host-path-file.json`;
- `filter_dataset-host-file.json`;
- `sort-dns-format-summary.json`;
- `sort-host-format-summary.json`;
- `sort-path-dns-file.json`;
- `sort-path-host-file.json`;
- `analysis-*-summary.json`.

### 6.2. Documentation

Content-analysis handlers write markdown files to:

- `docs/ru/analysis-dataset/...`;
- `docs/en/analysis-dataset/...`.

For each format, the code usually creates:

- a detailed format document;
- a `README.md` with a summary table for the directory.

### 6.3. Reports

Reports are written under `PATH_REPORT` using paths from `config.py`, for example:

```text
reports/ru/stage-one/analysis-dataset/host/train
reports/en/stage-one/analysis-dataset/dns/train
```

## 7. Management Commands

### 7.1. Initial Analysis

```bash
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers analyze-dataset dns-dataset-handler
```

### 7.2. Host Filtering

```bash
python manage.py handlers filter-dataset filter-host-dataset-handler
```

### 7.3. Sorting

```bash
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
```

### 7.4. Exporting Paths After Sorting

```bash
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
```

### 7.5. DNS Analysis

```bash
python manage.py handlers dns-analyze analyze-train-csv-content
python manage.py handlers dns-analyze analyze-train-pcap-content
python manage.py handlers dns-analyze analyze-train-pcap-csv-content
python manage.py handlers dns-analyze analyze-test-csv-content
python manage.py handlers dns-analyze analyze-test-pcap-content
python manage.py handlers dns-analyze analyze-test-pcap-csv-content
python manage.py handlers dns-analyze analyze-validation-pcap-content
python manage.py handlers dns-analyze analyze-validation-txt-content
```

### 7.6. Host Analysis

Host commands follow this shape:

```bash
python manage.py handlers host-analyze <action>
```

Examples:

```bash
python manage.py handlers host-analyze analyze-csv-content
python manage.py handlers host-analyze analyze-test-json-content
python manage.py handlers host-analyze analyze-validation-pcapng-content
```

The full command list is stored in `config.py` in the `manage_commands` variable.

## 8. Adding a New Handler

### 8.1. New DNS Format

1. Add a handler file under `scripts/handlers/dns_analyze/`.
2. Implement a result dataclass and a handler class with `analyze_and_generate_docs()`.
3. Read input paths from `sort-path-dns-file.json`.
4. Generate summary JSON, RU/EN docs, and RU/EN reports.
5. Add the class import to `scripts/handlers/dns_analyze/__init__.py`.
6. Add a launch function to `scripts/handlers/dns_analyze/run_action.py`.
7. Add the action to `scripts/handlers/dns_analyze/router_dns.py`.
8. Add the command to `manage_commands`.

### 8.2. New Host Format

1. Check that `HostDatasetSortHandler._detect_format_group()` can detect the format.
2. Add a handler file under `scripts/handlers/host_analyze/`.
3. Implement `analyze_and_generate_docs()`.
4. Export the class from `scripts/handlers/host_analyze/__init__.py`.
5. Add a launch function to `scripts/handlers/host_analyze/run_action.py`.
6. Add the action to `scripts/handlers/host_analyze/router_host.py`.
7. Add the command to `manage_commands`.

## 9. Technical Constraints and Risks

### 9.1. Strong Coupling Through `config.py`

Most code receives paths from `config.py`. This simplifies CLI execution, but makes isolated handler testing harder and increases the impact of configuration mistakes.

### 9.2. Intermediate State Is Stored in JSON

Pipeline stages depend on files under `PATH_TEMP_DATA`. If a JSON file is stale or was produced for a different dataset snapshot, later stages may process incorrect input.

### 9.3. Routing Uses Long `if/elif` Chains

This approach is simple, but does not scale well. Adding a new action requires synchronized changes in the router, `run_action.py`, `__init__.py`, and `manage_commands`.

### 9.4. Detected Configuration Inconsistencies

The current `config.py` has places that should be checked before production use:

- `PATH_FILTER_LOG = f"{PATH_DATA_STORAGE}/logs/filter_log",` creates a tuple because of the trailing comma, not a string.
- `DOCS_RU_ANALYSIS_DNS_TRAIN` points to `docs/ru/analysis-dataset/host/train`, although its name indicates the DNS train directory.

These issues can cause logs or DNS train documentation to be written to unexpected locations.

### 9.5. No Shared Base Abstraction for Content Analysis

Many handlers repeat the same pattern:

- read `sort-path-*-file.json`;
- sample files;
- build a summary;
- write markdown;
- write reports.

This works, but the maintenance cost grows as more formats are added.

## 10. Improvement Recommendations

1. Replace `if/elif` routers with dictionaries mapping action names to callables. This reduces the risk of mistakes when adding commands.
2. Extract common content-analysis behavior into a base class or composable helper functions.
3. Add automated tests for:
   - dataset role detection;
   - format group detection;
   - Host file filtering;
   - JSON read/write behavior;
   - documentation path generation.
4. Validate `config.py` at CLI startup and report empty or invalid environment variables explicitly.
5. Add versioning or timestamp metadata to JSON artifacts to avoid using stale intermediate state.
6. Fix the configuration inconsistencies listed in the risks section.
