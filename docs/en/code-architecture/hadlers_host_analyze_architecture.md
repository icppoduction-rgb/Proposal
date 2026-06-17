# Handler: `host_analyze`

## Purpose

`host_analyze` analyzes host buckets prepared by `analyze_dataset -> filter_dataset -> sort -> save_sort`. Each action maps to a concrete role and file format/type.

## CLI

```powershell
python manage.py handlers host-analyze <action>
```

## Components

| File | Purpose |
|---|---|
| `scripts/handlers/host_analyze/router_host.py` | Action -> analyzer class map. |
| `scripts/handlers/host_analyze/run_action.py` | Shared analyzer execution and result printing. |
| `scripts/handlers/host_analyze/analyze_host_*_dataset_handler.py` | Concrete host bucket analyzers. |

## Inputs

| Artifact | Purpose |
|---|---|
| `PATH_TEMP_DATA/sort-path-host-file.json` | `role -> format -> paths` map created by `save-sort-host-dataset-handler`. |
| Files from the sorted tree | Actual host file contents analyzed by the concrete handler. |

## TRAIN Actions

TRAIN actions in the router do not use a `train` prefix; the role is set inside the corresponding analyzer.

| Format/scope | Action |
|---|---|
| csv | `analyze-csv-content` |
| auth.log | `analyze-auth-log-content` |
| cpu.log | `analyze-cpu-log-content` |
| diskio.log | `analyze-diskio-log-content` |
| filesystem.log | `analyze-filesystem-log-content` |
| fsstat.log | `analyze-fsstat-log-content` |
| ghc | `analyze-ghc-content` |
| info | `analyze-info-content` |
| journal | `analyze-journal-content` |
| journal~ | `analyze-journal-tilde-content` |
| json | `analyze-json-content` |
| json-1 | `analyze-json-1-content` |
| load.log | `analyze-load-log-content` |
| log | `analyze-log-content` |
| log-1 | `analyze-log-1-content` |
| log-2 | `analyze-log-2-content` |
| log-3 | `analyze-log-3-content` |
| mail.info-1 | `analyze-mail-info-1-content` |
| mail.warn-1 | `analyze-mail-warn-1-content` |
| mainlog | `analyze-mainlog-content` |
| mainlog-1 | `analyze-mainlog-1-content` |
| mainlog-2 | `analyze-mainlog-2-content` |
| mainlog-3 | `analyze-mainlog-3-content` |
| memory.log | `analyze-memory-log-content` |
| messages | `analyze-messages-content` |
| messages-1 | `analyze-messages-1-content` |
| netflow.ids | `analyze-netflow-ids-content` |
| network.log | `analyze-network-log-content` |
| pcap | `analyze-pcap-content` |
| process.log | `analyze-process-log-content` |
| process.summary.log | `analyze-process-summary-log-content` |
| sc | `analyze-sc-content` |
| service.log | `analyze-service-log-content` |
| socket.summary.log | `analyze-socket-summary-log-content` |
| syslog | `analyze-syslog-content` |
| syslog-1 | `analyze-syslog-1-content` |
| syslog-2 | `analyze-syslog-2-content` |
| syslog-3 | `analyze-syslog-3-content` |
| syslog-4 | `analyze-syslog-4-content` |
| syslog.log | `analyze-syslog-log-content` |
| txt | `analyze-txt-content` |
| uptime.log | `analyze-uptime-log-content` |
| xml | `analyze-xml-content` |

## TEST Actions

| Format/scope | Action |
|---|---|
| bson | `analyze-test-bson-content` |
| csv | `analyze-test-csv-content` |
| json | `analyze-test-json-content` |
| log | `analyze-test-log-content` |
| netflow_day | `analyze-test-netflow-day-content` |
| txt | `analyze-test-txt-content` |
| wls_day | `analyze-test-wls-day-content` |

## VALIDATION Actions

| Format/scope | Action |
|---|---|
| cap | `analyze-validation-cap-content` |
| csv | `analyze-validation-csv-content` |
| json | `analyze-validation-json-content` |
| netflow_day | `analyze-validation-netflow-day-content` |
| pcap | `analyze-validation-pcap-content` |
| pcapng | `analyze-validation-pcapng-content` |
| txt | `analyze-validation-txt-content` |
| wls_day | `analyze-validation-wls-day-content` |

## Outputs

Each analyzer creates a summary JSON in `PATH_TEMP_DATA` and Markdown/text reports in docs/report directories from `config.py`. Summary names follow:

```text
analysis-host-<role>-<format>-summary.json
```

The exact field set depends on the analyzer, but typically includes source JSON path, role, format, file count, status, detected columns/fields, sample records, error/skipped counters, and a blocking reason.

## Pipeline Position

```text
Host source files
  -> analyze-dataset host-dataset-handler
  -> filter-dataset filter-host-dataset-handler
  -> sort sort-host-dataset-handler
  -> save-sort save-sort-host-dataset-handler
  -> host-analyze <role/format action>
```

`host_analyze` does not create normalized Parquet and does not register the PostgreSQL Catalog. Its outputs are an exploratory basis for Stage Two parser implementation.

## Relation to Stage Two

Stage One analysis remains separate from Stage Two normalization. `netflow_day`, `netflow_ids`, and `wls_day` have Stage One content-analysis handlers and are normalized in Stage Two through `HostNetflowParser` when catalog rows are marked `READY_FOR_PARSING` and an active registry entry is available.
