# Handlers Architecture: host_analyze

## Table of Contents

- [1. Purpose](#1-purpose)
- [2. Package Files](#2-package-files)
- [3. Service Startup](#3-service-startup)
- [4. General Call Chain](#4-general-call-chain)
- [5. Router and run_action](#5-router-and-run_action)
- [6. Common Host Content-Analysis Handler Contract](#6-common-host-content-analysis-handler-contract)
- [7. Host TRAIN Handlers](#7-host-train-handlers)
- [8. Host TEST Handlers](#8-host-test-handlers)
- [9. Host VALIDATION Handlers](#9-host-validation-handlers)
- [10. Inheritance and Logic Reuse](#10-inheritance-and-logic-reuse)
- [11. Output Artifacts](#11-output-artifacts)
- [12. Errors and Limitations](#12-errors-and-limitations)

## 1. Purpose

`scripts/handlers/host_analyze` analyzes sorted Host file contents and generates technical documentation for each format. The service runs after:

1. `analyze-dataset host-dataset-handler`;
2. `filter-dataset filter-host-dataset-handler`;
3. `sort sort-host-dataset-handler`;
4. `save-sort save-sort-host-dataset-handler`.

Main input for all Host analysis handlers:

```text
PATH_TEMP_DATA/sort-path-host-file.json
```

## 2. Package Files

| File group | Purpose |
|---|---|
| `router_host.py` | Maps string actions to run functions. |
| `run_action.py` | Instantiates handler classes and prints results. |
| `__init__.py` | Exports all Host content-analysis handlers. |
| `analyze_host_*_dataset_handler.py` | Analyzes a specific role/format bucket. |

The package covers three groups:

- Host `TRAIN`;
- Host `TEST`;
- Host `VALIDATION`.

## 3. Service Startup

Format:

```bash
python manage.py handlers host-analyze <action>
```

Examples:

```bash
python manage.py handlers host-analyze analyze-csv-content
python manage.py handlers host-analyze analyze-test-json-content
python manage.py handlers host-analyze analyze-validation-pcapng-content
```

## 4. General Call Chain

```text
python manage.py handlers host-analyze <action>
-> manage.manage()
-> router_commands("handlers", "host-analyze", action)
-> router_commands_handlers("host-analyze", action)
-> router_host(action)
-> analyze_*_content()
-> Host*ContentAnalysisHandler(PATH_TEMP_DATA, PROJECT_ROOT, PATH_REPORT)
-> analyze_and_generate_docs()
-> _read_source_json() / _read_host_source_json()
-> _extract_*_paths(...) / _extract_paths(...)
-> _select_sample_paths(...)
-> _build_summary(...)
-> JsonDataManager(summary_json).write(...)
-> _build_ru_markdown(...) / _build_en_markdown(...) / _build_markdown(...)
-> _build_ru_readme(...) / _build_en_readme(...) / _build_readme(...)
-> _build_ru_report(...) / _build_en_report(...) / _build_report(...)
-> _write_text_file(...)
-> print_data(...)
```

## 5. Router and run_action

### `router_host(action: str)`

`router_host` contains a long `if/elif` chain. Each branch compares `action` with a command string and calls a function from `run_action.py`.

Unknown actions print `manage_commands`.

### `run_action.py`

Each run function:

1. Instantiates a concrete handler class.
2. Passes:
   - `temp_data_path=PATH_TEMP_DATA`;
   - `project_root=PROJECT_ROOT`;
   - `report_path=PATH_REPORT`.
3. Calls `handler.analyze_and_generate_docs()`.
4. Sends the result to `print_data()`.

`print_data()` prints:

- summary JSON;
- RU/EN docs;
- RU/EN README;
- RU/EN reports;
- total files;
- sampled files;
- status.

## 6. Common Host Content-Analysis Handler Contract

### Input JSON

```json
{
  "TRAIN": {
    "csv": ["/absolute/path/file.csv"]
  },
  "TEST": {},
  "VALIDATION": {}
}
```

### Result Dataclass

Almost every handler returns a dataclass with:

- `summary_json_file`;
- `docs_ru_file`;
- `docs_en_file`;
- `docs_ru_readme_file`;
- `docs_en_readme_file`;
- `report_ru_file`;
- `report_en_file`;
- `total_files_count`;
- `sampled_files_count`;
- `status`.

### Typical Methods

| Method | Purpose |
|---|---|
| `analyze_and_generate_docs()` | Main orchestration method. |
| `_read_source_json()` / `_read_host_source_json()` | Reads `sort-path-host-file.json`. |
| `_extract_paths()` / `_extract_<format>_paths()` | Extracts paths for the target role and format. |
| `_select_sample_paths()` | Selects a sample for large datasets. |
| `_build_summary()` | Builds technical summary. |
| `_detect_encoding()` | Selects encoding for text files. |
| `_infer_type()` / `_safe_extract_numeric()` | Infers types or numeric values. |
| `_build_ru_markdown()` / `_build_en_markdown()` / `_build_markdown()` | Generates documentation. |
| `_build_ru_readme()` / `_build_en_readme()` / `_build_readme()` | Generates directory index. |
| `_build_ru_report()` / `_build_en_report()` / `_build_report()` | Generates report. |
| `_load_host_format_counts()` / `_load_host_test_format_counts()` / `_load_counts()` | Loads count summaries. |
| `_load_optional_status()` | Loads status from another analysis. |
| `_summary_json_excerpt()` | Prepares a short JSON excerpt for reports. |
| `_write_text_file()` | Creates directory and writes markdown. |

## 7. Host TRAIN Handlers

Actions without `test` or `validation` prefixes target Host TRAIN.

| Action | Handler | Main task |
|---|---|---|
| `analyze-csv-content` | `HostCSVContentAnalysisHandler` | CSV schema, delimiter, header, field statistics. |
| `analyze-auth-log-content` | `HostAuthLogContentAnalysisHandler` | Auth log messages, actions, host/security indicators. |
| `analyze-cpu-log-content` | `HostCPULogContentAnalysisHandler` | CPU numeric metrics. |
| `analyze-diskio-log-content` | `HostDiskioLogContentAnalysisHandler` | Disk IO numeric metrics. |
| `analyze-filesystem-log-content` | `HostFilesystemLogContentAnalysisHandler` | Filesystem metrics and status. |
| `analyze-fsstat-log-content` | `HostFSStatLogContentAnalysisHandler` | FS stat metrics. |
| `analyze-ghc-content` | `HostGHCContentAnalysisHandler` | GHC/scenario-like host traces. |
| `analyze-info-content` | `HostInfoContentAnalysisHandler` | Info messages and action markers. |
| `analyze-journal-content` | `HostJournalContentAnalysisHandler` | Journal-style text statistics. |
| `analyze-journal-tilde-content` | `HostJournalTildeContentAnalysisHandler` | `journal~` rotated/backup variant. |
| `analyze-json-content` | `HostJSONContentAnalysisHandler` | JSON/raw JSON-like files. |
| `analyze-json-1-content` | `HostJSON1ContentAnalysisHandler` | `json-1` rotated variant. |
| `analyze-load-log-content` | `HostLoadLogContentAnalysisHandler` | Load metrics. |
| `analyze-log-content` | `HostLogContentAnalysisHandler` | Generic log files. |
| `analyze-log-1-content` | `HostLog1ContentAnalysisHandler` | Rotated `log-1`. |
| `analyze-log-2-content` | `HostLog2ContentAnalysisHandler` | Rotated `log-2`. |
| `analyze-log-3-content` | `HostLog3ContentAnalysisHandler` | Rotated `log-3`. |
| `analyze-mail-info-1-content` | `HostMailInfo1ContentAnalysisHandler` | Mail info logs. |
| `analyze-mail-warn-1-content` | `HostMailWarn1ContentAnalysisHandler` | Mail warning logs. |
| `analyze-mainlog-content` | `HostMainlogContentAnalysisHandler` | Main logs. |
| `analyze-mainlog-1-content` | `HostMainlog1ContentAnalysisHandler` | Rotated mainlog-1. |
| `analyze-mainlog-2-content` | `HostMainlog2ContentAnalysisHandler` | Rotated mainlog-2. |
| `analyze-mainlog-3-content` | `HostMainlog3ContentAnalysisHandler` | Rotated mainlog-3. |
| `analyze-memory-log-content` | `HostMemoryLogContentAnalysisHandler` | Memory metrics. |
| `analyze-messages-content` | `HostMessagesContentAnalysisHandler` | System messages. |
| `analyze-messages-1-content` | `HostMessages1ContentAnalysisHandler` | Rotated messages-1. |
| `analyze-netflow-ids-content` | `HostNetflowIdsContentAnalysisHandler` | Netflow id files. |
| `analyze-network-log-content` | `HostNetworkLogContentAnalysisHandler` | Network metrics. |
| `analyze-pcap-content` | `HostPCAPContentAnalysisHandler` | PCAP-like host files. |
| `analyze-process-log-content` | `HostProcessLogContentAnalysisHandler` | Process metrics/logs. |
| `analyze-process-summary-log-content` | `HostProcessSummaryLogContentAnalysisHandler` | Process summary metrics. |
| `analyze-sc-content` | `HostSCContentAnalysisHandler` | SC trace format. |
| `analyze-service-log-content` | `HostServiceLogContentAnalysisHandler` | Service metrics/logs. |
| `analyze-socket-summary-log-content` | `HostSocketSummaryLogContentAnalysisHandler` | Socket summary metrics. |
| `analyze-syslog-content` | `HostSyslogContentAnalysisHandler` | Syslog format. |
| `analyze-syslog-1-content` | `HostSyslog1ContentAnalysisHandler` | Rotated syslog-1. |
| `analyze-syslog-2-content` | `HostSyslog2ContentAnalysisHandler` | Rotated syslog-2. |
| `analyze-syslog-3-content` | `HostSyslog3ContentAnalysisHandler` | Rotated syslog-3. |
| `analyze-syslog-4-content` | `HostSyslog4ContentAnalysisHandler` | Rotated syslog-4. |
| `analyze-syslog-log-content` | `HostSyslogLogContentAnalysisHandler` | `syslog.log` semantic format. |
| `analyze-txt-content` | `HostTXTContentAnalysisHandler` | Text host traces. |
| `analyze-uptime-log-content` | `HostUptimeLogContentAnalysisHandler` | Uptime metrics. |
| `analyze-xml-content` | `HostXMLContentAnalysisHandler` | XML content structure. |

### TRAIN Handler Patterns

TRAIN handlers fall into several types:

- CSV-specific: `HostCSVContentAnalysisHandler` uses `CSVFileProbe`, delimiter/header detection, and field statistics.
- Numeric log handlers: CPU, diskio, filesystem, fsstat, load, memory, network, process, service, socket, uptime extract numeric signals and statistics.
- Text/log handlers: auth, info, journal, log, mail, messages, syslog analyze lines, prefix/action patterns, and examples.
- Structured handlers: JSON/XML/PCAP/SC/GHC build summaries from structure or technical format attributes.

## 8. Host TEST Handlers

| Action | Handler | Important classes/methods |
|---|---|---|
| `analyze-test-bson-content` | `HostTestBSONContentAnalysisHandler` | `BSONFileProbe`, `BSONDocumentProbe.parse_many()`, `_parse_document()` |
| `analyze-test-csv-content` | `HostTestCSVContentAnalysisHandler` | `CSVProbe`, `_probe_file()`, `_infer_type()` |
| `analyze-test-json-content` | `HostTestJSONContentAnalysisHandler` | `JSONProbe`, `_parse_json_like()`, `_classify_schema()`, `_collect_record()` |
| `analyze-test-log-content` | `HostTestLogContentAnalysisHandler` | `LogProbe`, `_message_prefix()`, `_render_counter_rows()` |
| `analyze-test-netflow-day-content` | `HostTestNetflowDayContentAnalysisHandler` | `NetflowDayProbe`, `_infer_type()`, `_render_fields()` |
| `analyze-test-txt-content` | `HostTestTXTContentAnalysisHandler` | `TXTProbe`, `_parse_key_value_line()`, `_infer_type()` |
| `analyze-test-wls-day-content` | `HostTestWLSDayContentAnalysisHandler` | `WLSDayProbe`, `_format_example()`, `_render_fields()` |

TEST handlers usually write documents to:

```text
docs/ru/analysis-dataset/host/test
docs/en/analysis-dataset/host/test
```

## 9. Host VALIDATION Handlers

| Action | Handler | Important classes/methods |
|---|---|---|
| `analyze-validation-cap-content` | `HostValidationCAPContentAnalysisHandler` | `CAPProbe`, `_probe_cap()`, `_decode_ethernet_packet()` |
| `analyze-validation-csv-content` | `HostValidationCSVContentAnalysisHandler` | `_extract_paths()`, `_build_summary()`, `_fields_table()` |
| `analyze-validation-json-content` | `HostValidationJSONContentAnalysisHandler` | `_collect_record()`, `_get_nested()`, `_format_example()` |
| `analyze-validation-netflow-day-content` | `HostValidationNetflowDayContentAnalysisHandler` | inherits TEST netflow logic |
| `analyze-validation-pcap-content` | `HostValidationPCAPContentAnalysisHandler` | inherits CAP logic |
| `analyze-validation-pcapng-content` | `HostValidationPCAPNGContentAnalysisHandler` | `PCAPNGProbe`, `_probe_pcapng()`, `_decode_ethernet_packet()` |
| `analyze-validation-txt-content` | `HostValidationTXTContentAnalysisHandler` | inherits TEST txt logic |
| `analyze-validation-wls-day-content` | `HostValidationWLSDayContentAnalysisHandler` | inherits TEST wls_day logic |

VALIDATION handlers write documents to:

```text
docs/ru/analysis-dataset/host/validation
docs/en/analysis-dataset/host/validation
```

## 10. Inheritance and Logic Reuse

`host_analyze` includes explicit inheritance:

| Class | Inherits from | Purpose |
|---|---|---|
| `HostValidationNetflowDayContentAnalysisHandler` | `HostTestNetflowDayContentAnalysisHandler` | Reuses netflow_day parsing for validation. |
| `HostValidationPCAPContentAnalysisHandler` | `HostValidationCAPContentAnalysisHandler` | Reuses packet/cap analysis logic for pcap. |
| `HostValidationTXTContentAnalysisHandler` | `HostTestTXTContentAnalysisHandler` | Reuses txt parsing. |
| `HostValidationWLSDayContentAnalysisHandler` | `HostTestWLSDayContentAnalysisHandler` | Reuses wls_day parsing. |

Beyond inheritance, many handlers share the same method structure. This makes the code easy to follow, but duplicates markdown/readme/report generation logic.

## 11. Output Artifacts

Typical outputs:

```text
PATH_TEMP_DATA/analysis-host-*-summary.json
docs/ru/analysis-dataset/host/<role>/<format>.md
docs/en/analysis-dataset/host/<role>/<format>.md
docs/ru/analysis-dataset/host/<role>/README.md
docs/en/analysis-dataset/host/<role>/README.md
PATH_REPORT/ru/stage-one/analysis-dataset/host/<role>/*.md
PATH_REPORT/en/stage-one/analysis-dataset/host/<role>/*.md
```

Status usually uses:

- `READY_FOR_FEATURE_EXTRACTION`;
- `PARTIALLY_SUPPORTED`;
- `NEEDS_CUSTOM_PARSER`;
- `BROKEN_OR_EMPTY`.

## 12. Errors and Limitations

- All handlers depend on a fresh `sort-path-host-file.json`.
- If the target format is absent from JSON, some handlers raise `ValueError`.
- Large datasets are analyzed through sampling, so summary reflects a sample.
- Binary/packet formats are handled through technical probing and do not replace specialized parsers.
- Adding a new Host format requires synchronized changes in the handler file, `__init__.py`, `run_action.py`, `router_host.py`, `manage_commands`, and possibly `HostDatasetSortHandler._detect_format_group()`.
- The package contains repeated markdown/report generation code; documentation structure changes may require editing multiple handlers.
