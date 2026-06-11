# Command Router Architecture

## Table of Contents

- [1. Document Purpose](#1-document-purpose)
- [2. Command Model](#2-command-model)
- [3. Command Execution Path](#3-command-execution-path)
- [4. `module` Level](#4-module-level)
- [5. `service` Level](#5-service-level)
- [6. `action` Level](#6-action-level)
- [7. `analyze-dataset` Routes](#7-analyze-dataset-routes)
- [8. `filter-dataset` Routes](#8-filter-dataset-routes)
- [9. `sort` Routes](#9-sort-routes)
- [10. `save-sort` Routes](#10-save-sort-routes)
- [11. `dns-analyze` Routes](#11-dns-analyze-routes)
- [12. `host-analyze` Routes](#12-host-analyze-routes)
- [13. Unknown Command Behavior](#13-unknown-command-behavior)
- [14. Route Dependencies on Configuration](#14-route-dependencies-on-configuration)
- [15. Adding a New Route](#15-adding-a-new-route)
- [16. Technical Notes](#16-technical-notes)

## 1. Document Purpose

This document describes how commands from `manage.py` move through routers in `scripts/*`, which `service` and `action` values are supported, which handlers are called, and which input/output artifacts each route expects.

Routes are implemented without a dedicated CLI framework. The command is parsed through `argparse`, then passed into a chain of router functions. Each router compares string arguments with supported command names through `if/elif` branches.

## 2. Command Model

Base format:

```bash
python manage.py <module> <service> <action>
```

The current code supports one `module` value:

```bash
python manage.py handlers <service> <action>
```

Arguments:

| Argument | Source | Purpose |
|---|---|---|
| `module` | `manage.py` | Top-level command namespace. The only active value is `handlers`. |
| `service` | `scripts/handlers/router_handler.py` | Command group: analysis, filtering, sorting, path export, or content analysis. |
| `action` | service-specific router | Concrete operation inside the selected service. |

`manage.py` uses `parse_known_args()`, so extra unknown arguments do not fail argparse and are currently ignored.

## 3. Command Execution Path

General call chain:

```text
python manage.py handlers <service> <action>
        |
        v
manage.manage()
        |
        v
scripts.router_script.router_commands(module, service, action)
        |
        v
scripts.handlers.router_handler.router_commands_handlers(service, action)
        |
        v
service router
        |
        v
run function
        |
        v
handler class
```

Example for DNS train CSV analysis:

```text
python manage.py handlers dns-analyze analyze-train-csv-content
        |
        v
router_commands("handlers", "dns-analyze", "analyze-train-csv-content")
        |
        v
router_commands_handlers("dns-analyze", "analyze-train-csv-content")
        |
        v
router_dns("analyze-train-csv-content")
        |
        v
analyze_train_csv_content()
        |
        v
DNSTrainCSVContentAnalysisHandler(...).analyze_and_generate_docs()
```

## 4. `module` Level

File:

- `scripts/router_script.py`

Logic:

```python
if module == "handlers":
    router_commands_handlers(service, action)
else:
    console.print(manage_commands)
```

Supported values:

| `module` | Result |
|---|---|
| `handlers` | The command is passed to `scripts.handlers.router_handler.router_commands_handlers`. |
| any other value or `None` | `manage_commands` help text is printed. |

This level does not validate `service` or `action`; both are passed downstream as strings or `None`.

## 5. `service` Level

File:

- `scripts/handlers/router_handler.py`

`router_commands_handlers(service, action)` selects one service router.

| `service` | Router | Purpose |
|---|---|---|
| `analyze-dataset` | `router_analyze(action)` | Initial scan of source DNS/Host datasets. |
| `filter-dataset` | `router_filter(action)` | Host dataset filtering based on project rules. |
| `sort` | `router_sort(action)` | File materialization by role and format. |
| `save-sort` | `router_save(action)` | Path export from the sorted tree to JSON. |
| `dns-analyze` | `router_dns(action)` | DNS content analysis and documentation generation. |
| `host-analyze` | `router_host(action)` | Host content analysis and documentation generation. |
| any other value or `None` | `manage_commands` | Help text is printed. |

## 6. `action` Level

`action` is selected inside the router for the chosen service. The common pattern is:

1. Router compares `action` with a known string.
2. On match, it calls a run function.
3. The run function instantiates a handler class.
4. The handler performs the business logic.
5. The router/runner prints a short execution result.

For `dns-analyze` and `host-analyze`, there is an additional `run_action.py` layer: the router calls a run function, and the run function creates the content-analysis handler.

## 7. `analyze-dataset` Routes

File:

- `scripts/handlers/analyze_dataset/router_analyze.py`

Service purpose: scan source dataset directories and persist JSON lists of paths and file names.

| Action | Function | Handler | Main inputs | Main outputs |
|---|---|---|---|---|
| `dns-dataset-handler` | `dns_dataset_handler()` | `DNSDatasetHandler` | `PATH_DNS_DATASETS`, `PATH_TEMP_DATA` | `dns-path-file.json`, `dns-file.json` |
| `host-dataset-handler` | `host_dataset_handler()` | `HostDatasetHandler` | `PATH_HOST_DATASETS`, `PATH_TEMP_DATA` | `host-path-file.json`, `host-file.json` |

DNS route logic:

1. Instantiate `DNSDatasetHandler`.
2. Recursively scan `PATH_DNS_DATASETS`.
3. Infer the role from path tokens: `TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`.
4. Write the result to JSON.
5. Print the JSON file paths.

Host route logic:

1. Instantiate `HostDatasetHandler`.
2. Recursively scan `PATH_HOST_DATASETS`.
3. Infer the role from path tokens: `TRAIN`, `TEST`, `VALIDATION`.
4. Unrecognized Host paths are assigned to `TEST`.
5. Write the result to JSON.

## 8. `filter-dataset` Routes

File:

- `scripts/handlers/filter_dataset/router_filter.py`

Service purpose: filter Host files after the initial dataset scan.

| Action | Function | Handler | Main inputs | Main outputs |
|---|---|---|---|---|
| `filter-host-dataset-handler` | `filter_host_dataset_handler()` | `HostDatasetFilterHandler` | `PATH_TEMP_DATA`, `PATH_FILTER_LOG` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`, exclusion log |

Route logic:

1. Instantiate `HostDatasetFilterHandler`.
2. Read `host-path-file.json` and `host-file.json`.
3. Extract the dataset name for each path.
4. Check whether the dataset is allowed for the role.
5. Check whether the file extension is allowed.
6. Write excluded files to the log with a reason.
7. Persist kept files to `filter_dataset-host-*.json`.

This stage is used only by the Host pipeline. The DNS pipeline goes directly from `analyze-dataset` to `sort`.

## 9. `sort` Routes

File:

- `scripts/handlers/sort/router_sort.py`

Service purpose: materialize a file tree grouped by role and format.

| Action | Function | Handler | Main inputs | Main outputs |
|---|---|---|---|---|
| `sort-host-dataset-handler` | `sort_host_dataset_handler()` | `HostDatasetSortHandler` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`, `PATH_HOST_DATASETS_FILTER` | tree `PATH_HOST_DATASETS_FILTER/<ROLE>/<format>/`, `sort-host-format-summary.json` |
| `sort-dns-dataset-handler` | `sort_dns_dataset_handler()` | `DNSDatasetSortHandler` | `dns-path-file.json`, `dns-file.json`, `PATH_DNS_DATASETS_FILTER` | tree `PATH_DNS_DATASETS_FILTER/<ROLE>/<format>/`, `sort-dns-format-summary.json` |

Route logic:

1. Instantiate the sort handler.
2. Validate the target directory.
3. Read JSON lists of paths and names.
4. Validate required roles.
5. Detect the format group from the file name.
6. Create the `<ROLE>/<format>` directory.
7. Try to create a hardlink with `os.link`.
8. If hardlink creation fails, copy the file with `shutil.copy2`.
9. If a name collision occurs, add a hash derived from the source path.
10. Write a summary JSON with metrics.

Result metrics:

- `created_links_count`;
- `copied_files_count`;
- `skipped_existing_count`;
- `missing_source_count`;
- `name_mismatch_count`;
- `files_by_role_and_format`.

## 10. `save-sort` Routes

File:

- `scripts/handlers/save_sort/router_save.py`

Service purpose: scan the sorted tree and persist grouped paths to JSON.

| Action | Function | Handler | Main inputs | Main outputs |
|---|---|---|---|---|
| `save-sort-host-dataset-handler` | `save_sort_host_dataset_handler()` | `HostSortedPathExportHandler` | `PATH_HOST_DATASETS_FILTER`, `PATH_TEMP_DATA` | `sort-path-host-file.json`, `sort-path-host-file-summary.json` |
| `save-sort-dns-dataset-handler` | `save_sort_dns_dataset_handler()` | `DNSSortedPathExportHandler` | `PATH_DNS_DATASETS_FILTER`, `PATH_TEMP_DATA` | `sort-path-dns-file.json`, `sort-path-dns-file-summary.json` |

Route logic:

1. Instantiate the export handler.
2. Validate that the sorted directory exists.
3. For each role, scan format directories.
4. Collect absolute file paths.
5. Write JSON shaped as `role -> format -> list[path]`.
6. Write a summary with counts by role and format.

## 11. `dns-analyze` Routes

Files:

- `scripts/handlers/dns_analyze/router_dns.py`;
- `scripts/handlers/dns_analyze/run_action.py`.

Service purpose: analyze sorted DNS file contents and generate summary JSON, RU/EN docs, and RU/EN reports.

Common route logic:

1. `router_dns(action)` selects a run function.
2. The run function instantiates the matching DNS content-analysis handler.
3. The handler receives `PATH_TEMP_DATA`, `PROJECT_ROOT`, and `PATH_REPORT`.
4. The handler reads `sort-path-dns-file.json`.
5. The handler selects the target role and format.
6. The handler analyzes all files or a sample.
7. Summary JSON, documentation, and reports are generated.
8. `print_data()` prints artifact paths and status.

| Action | Run function | Handler | Role | Format |
|---|---|---|---|---|
| `analyze-train-csv-content` | `analyze_train_csv_content()` | `DNSTrainCSVContentAnalysisHandler` | `TRAIN` | `csv` |
| `analyze-train-pcap-content` | `analyze_train_pcap_content()` | `DNSTrainPCAPContentAnalysisHandler` | `TRAIN` | `pcap` |
| `analyze-train-pcap-csv-content` | `analyze_train_pcap_csv_content()` | `DNSTrainPCAPCSVContentAnalysisHandler` | `TRAIN` | `pcap.csv` |
| `analyze-test-csv-content` | `analyze_test_csv_content()` | `DNSTestCSVContentAnalysisHandler` | `TEST` | `csv` |
| `analyze-test-pcap-content` | `analyze_test_pcap_content()` | `DNSTestPCAPContentAnalysisHandler` | `TEST` | `pcap` |
| `analyze-test-pcap-csv-content` | `analyze_test_pcap_csv_content()` | `DNSTestPCAPCSVContentAnalysisHandler` | `TEST` | `pcap.csv` |
| `analyze-validation-pcap-content` | `analyze_validation_pcap_content()` | `DNSValidationPCAPContentAnalysisHandler` | `VALIDATION` | `pcap` |
| `analyze-validation-txt-content` | `analyze_validation_txt_content()` | `DNSValidationTXTContentAnalysisHandler` | `VALIDATION` | `txt` |

## 12. `host-analyze` Routes

Files:

- `scripts/handlers/host_analyze/router_host.py`;
- `scripts/handlers/host_analyze/run_action.py`.

Service purpose: analyze sorted Host file contents and generate summary JSON, RU/EN docs, and RU/EN reports.

Common route logic:

1. `router_host(action)` selects a run function.
2. The run function instantiates the matching Host content-analysis handler.
3. The handler receives `PATH_TEMP_DATA`, `PROJECT_ROOT`, and `PATH_REPORT`.
4. The handler reads `sort-path-host-file.json`.
5. The handler selects the target role and format.
6. The handler analyzes all files or a sample.
7. Summary JSON, documentation, and reports are generated.
8. `print_data()` prints artifact paths and status.

### 12.1. Host TRAIN Routes

Actions without the `test` or `validation` prefix target Host TRAIN formats.

| Action | Handler |
|---|---|
| `analyze-csv-content` | `HostCSVContentAnalysisHandler` |
| `analyze-auth-log-content` | `HostAuthLogContentAnalysisHandler` |
| `analyze-cpu-log-content` | `HostCPULogContentAnalysisHandler` |
| `analyze-diskio-log-content` | `HostDiskioLogContentAnalysisHandler` |
| `analyze-filesystem-log-content` | `HostFilesystemLogContentAnalysisHandler` |
| `analyze-fsstat-log-content` | `HostFSStatLogContentAnalysisHandler` |
| `analyze-ghc-content` | `HostGHCContentAnalysisHandler` |
| `analyze-info-content` | `HostInfoContentAnalysisHandler` |
| `analyze-journal-content` | `HostJournalContentAnalysisHandler` |
| `analyze-journal-tilde-content` | `HostJournalTildeContentAnalysisHandler` |
| `analyze-json-content` | `HostJSONContentAnalysisHandler` |
| `analyze-json-1-content` | `HostJSON1ContentAnalysisHandler` |
| `analyze-load-log-content` | `HostLoadLogContentAnalysisHandler` |
| `analyze-log-content` | `HostLogContentAnalysisHandler` |
| `analyze-log-1-content` | `HostLog1ContentAnalysisHandler` |
| `analyze-log-2-content` | `HostLog2ContentAnalysisHandler` |
| `analyze-log-3-content` | `HostLog3ContentAnalysisHandler` |
| `analyze-mail-info-1-content` | `HostMailInfo1ContentAnalysisHandler` |
| `analyze-mail-warn-1-content` | `HostMailWarn1ContentAnalysisHandler` |
| `analyze-mainlog-content` | `HostMainlogContentAnalysisHandler` |
| `analyze-mainlog-1-content` | `HostMainlog1ContentAnalysisHandler` |
| `analyze-mainlog-2-content` | `HostMainlog2ContentAnalysisHandler` |
| `analyze-mainlog-3-content` | `HostMainlog3ContentAnalysisHandler` |
| `analyze-memory-log-content` | `HostMemoryLogContentAnalysisHandler` |
| `analyze-messages-content` | `HostMessagesContentAnalysisHandler` |
| `analyze-messages-1-content` | `HostMessages1ContentAnalysisHandler` |
| `analyze-netflow-ids-content` | `HostNetflowIdsContentAnalysisHandler` |
| `analyze-network-log-content` | `HostNetworkLogContentAnalysisHandler` |
| `analyze-pcap-content` | `HostPCAPContentAnalysisHandler` |
| `analyze-process-log-content` | `HostProcessLogContentAnalysisHandler` |
| `analyze-process-summary-log-content` | `HostProcessSummaryLogContentAnalysisHandler` |
| `analyze-sc-content` | `HostSCContentAnalysisHandler` |
| `analyze-service-log-content` | `HostServiceLogContentAnalysisHandler` |
| `analyze-socket-summary-log-content` | `HostSocketSummaryLogContentAnalysisHandler` |
| `analyze-syslog-content` | `HostSyslogContentAnalysisHandler` |
| `analyze-syslog-1-content` | `HostSyslog1ContentAnalysisHandler` |
| `analyze-syslog-2-content` | `HostSyslog2ContentAnalysisHandler` |
| `analyze-syslog-3-content` | `HostSyslog3ContentAnalysisHandler` |
| `analyze-syslog-4-content` | `HostSyslog4ContentAnalysisHandler` |
| `analyze-syslog-log-content` | `HostSyslogLogContentAnalysisHandler` |
| `analyze-txt-content` | `HostTXTContentAnalysisHandler` |
| `analyze-uptime-log-content` | `HostUptimeLogContentAnalysisHandler` |
| `analyze-xml-content` | `HostXMLContentAnalysisHandler` |

### 12.2. Host TEST Routes

| Action | Handler |
|---|---|
| `analyze-test-bson-content` | `HostTestBSONContentAnalysisHandler` |
| `analyze-test-csv-content` | `HostTestCSVContentAnalysisHandler` |
| `analyze-test-json-content` | `HostTestJSONContentAnalysisHandler` |
| `analyze-test-log-content` | `HostTestLogContentAnalysisHandler` |
| `analyze-test-netflow-day-content` | `HostTestNetflowDayContentAnalysisHandler` |
| `analyze-test-txt-content` | `HostTestTXTContentAnalysisHandler` |
| `analyze-test-wls-day-content` | `HostTestWLSDayContentAnalysisHandler` |

### 12.3. Host VALIDATION Routes

| Action | Handler |
|---|---|
| `analyze-validation-cap-content` | `HostValidationCAPContentAnalysisHandler` |
| `analyze-validation-csv-content` | `HostValidationCSVContentAnalysisHandler` |
| `analyze-validation-json-content` | `HostValidationJSONContentAnalysisHandler` |
| `analyze-validation-netflow-day-content` | `HostValidationNetflowDayContentAnalysisHandler` |
| `analyze-validation-pcap-content` | `HostValidationPCAPContentAnalysisHandler` |
| `analyze-validation-pcapng-content` | `HostValidationPCAPNGContentAnalysisHandler` |
| `analyze-validation-txt-content` | `HostValidationTXTContentAnalysisHandler` |
| `analyze-validation-wls-day-content` | `HostValidationWLSDayContentAnalysisHandler` |

## 13. Unknown Command Behavior

Each level falls back to help text:

- unknown `module` -> `manage_commands`;
- unknown `service` -> `manage_commands`;
- unknown `action` -> `manage_commands`.

The current implementation does not return an explicit non-zero exit code for unknown commands. It also does not raise an exception: the user sees help text, but CI/CD automation may not distinguish an invalid command from a successful run.

## 14. Route Dependencies on Configuration

Routes do not accept paths through CLI arguments. All paths come from `config.py`.

| Variable | Used by routes |
|---|---|
| `PATH_HOST_DATASETS` | `analyze-dataset host-dataset-handler` |
| `PATH_DNS_DATASETS` | `analyze-dataset dns-dataset-handler` |
| `PATH_TEMP_DATA` | almost all handlers; stores intermediate JSON |
| `PATH_HOST_DATASETS_FILTER` | `sort-host-dataset-handler`, `save-sort-host-dataset-handler` |
| `PATH_DNS_DATASETS_FILTER` | `sort-dns-dataset-handler`, `save-sort-dns-dataset-handler` |
| `PATH_FILTER_LOG` | `filter-host-dataset-handler` |
| `PROJECT_ROOT` | content-analysis handlers for documentation paths |
| `PATH_REPORT` | content-analysis handlers for reports |

Practical implication: `.env` or environment variables must be configured before running routes. Otherwise handlers may fail path validation or write artifacts to unexpected locations.

## 15. Adding a New Route

### 15.1. New Service

1. Create a new router in `scripts/handlers/<service>/router_<name>.py`.
2. Add a service-router function.
3. Import the router in `scripts/handlers/router_handler.py`.
4. Add an `elif service == "<service>"` branch.
5. Add the command to `manage_commands`.

### 15.2. New Action in an Existing Service

1. Implement the handler class or action function.
2. If the service uses `run_action.py`, add a run function there.
3. Import the run function in the router.
4. Add an `elif action == "<new-action>"` branch.
5. Add the command to `manage_commands`.
6. Verify which JSON artifacts must exist before the new route is run.

### 15.3. New Content-Analysis Route

For DNS:

1. Add the handler under `scripts/handlers/dns_analyze/`.
2. Export the class in `scripts/handlers/dns_analyze/__init__.py`.
3. Add a run function in `dns_analyze/run_action.py`.
4. Add the action in `dns_analyze/router_dns.py`.

For Host:

1. Add the handler under `scripts/handlers/host_analyze/`.
2. Export the class in `scripts/handlers/host_analyze/__init__.py`.
3. Add a run function in `host_analyze/run_action.py`.
4. Add the action in `host_analyze/router_host.py`.

## 16. Technical Notes

1. Router logic is simple and readable, but long `if/elif` blocks become fragile as the command set grows.
2. `manage.py` uses `parse_known_args()`, so extra arguments are ignored. For a stricter CLI, `parse_args()` would be safer.
3. Unknown commands print help text but do not signal failure through an exit code.
4. Routes do not have centralized validation of pipeline stage dependencies. For example, `dns-analyze` expects `sort-path-dns-file.json` to already exist.
5. Commands and router branches are duplicated in `manage_commands`; adding a route requires manually syncing code and help text.
6. For production maintenance, replacing `if/elif` routing with `action -> callable` dictionaries and adding a test that compares router commands with help text would reduce regression risk.
