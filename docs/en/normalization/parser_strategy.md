# Parser Registry and Parser Selection Strategy

Parser strategy has three parts:

1. `parser_registry_seed.json` describes supported parser groups.
2. `ParserRegistrySeeder` expands groups into `parser_registry` rows.
3. `ParserResolver` selects an active parser for a concrete `dataset_files` row by `branch`, `role`, and `source_format`.

## Registry Seed

File:

```text
scripts/stage_two/parser_registry/parser_registry_seed.json
```

Load it with:

```bash
python manage.py stage-two seed-parser-registry
```

The seeder verifies that `parser_module` and `parser_class` can be imported. If a class is missing or does not inherit from `BaseParser`, the entry can be stored as inactive with diagnostic metadata in `config_json.class_validation`.

## Parser Selection

`ParserResolver` searches active entries:

```text
branch == dataset_file.branch
source_format == dataset_file.source_format
supported_role == dataset_file.role OR supported_role IS NULL
is_active == true
```

It then sorts by `priority`, then `id`. A role-specific entry wins only through priority/order; a generic entry with `supported_role = NULL` matches all roles.

If no parser is found:

- `resolve_or_mark_unsupported()` marks the file as `UNSUPPORTED_FORMAT`;
- `normalize-format` returns status `UNSUPPORTED_FORMAT` for the selected bucket;
- parser runs must not pretend that normalization succeeded.

## Implemented Parser Groups

### DNS

| Parser class | Source formats | Roles | Module |
| --- | --- | --- | --- |
| `DnsCsvParser` | `csv` | all active roles | `scripts.stage_two.parsers.dns` |
| `DnsPcapCsvParser` | `pcap.csv` | all active roles | `scripts.stage_two.parsers.dns` |
| `DnsTxtDomainListParser` | `txt` | `VALIDATION` | `scripts.stage_two.parsers.dns` |
| `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` | all active roles | `scripts.stage_two.parsers.dns` |

### Host

| Parser class | Source formats | Roles | Module |
| --- | --- | --- | --- |
| `HostCsvParser` | `csv` | all active roles | `scripts.stage_two.parsers.host` |
| `HostJsonLinesParser` | `json`, `json-1` | all active roles | `scripts.stage_two.parsers.host` |
| `HostLineLogParser` | `auth.log`, `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `info`, `journal`, `journal~`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `uptime.log` | all active roles | `scripts.stage_two.parsers.host` |
| `HostSyscallTraceParser` | `txt`, `sc`, `ghc` | all active roles | `scripts.stage_two.parsers.host` |
| `HostXmlParser` | `xml` | all active roles | `scripts.stage_two.parsers.host` |
| `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` | all active roles | `scripts.stage_two.parsers.host` |
| `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` | `TRAIN`, `VALIDATION` | `scripts.stage_two.parsers.host` |
| `HostBsonSandboxParser` | `bson` | `TEST` | `scripts.stage_two.parsers.host` |

Metricbeat-like logs are handled through existing host parser modules/helpers; there is no separate active seed group named `HostMetricbeatParser` in the current registry seed.

## Parser Lifecycle Statuses

| Level | Status | Meaning |
| --- | --- | --- |
| parser run | `SUCCESS` | Parser completed and emitted events without failed rows. |
| parser run | `PARTIAL_SUCCESS` | Parser emitted events, but some rows/records failed. |
| parser run | `FAILED` | Parser failed for the file. |
| parser run | `SKIPPED` | File was intentionally skipped. |
| dataset file | `PARSED` | File was successfully normalized. |
| dataset file | `PARTIALLY_PARSED` | Normalized events exist, but errors occurred. |
| dataset file | `FAILED` | Normalization failed. |
| dataset file | `SKIPPED` | File was skipped by parser/result policy. |
| dataset file | `UNSUPPORTED_FORMAT` | No parser exists for `branch/role/source_format`. |

Stage One analysis statuses such as `READY_FOR_FEATURE_EXTRACTION`, `NEEDS_CUSTOM_PARSER`, `PARTIALLY_SUPPORTED`, and `BROKEN_OR_EMPTY` are input guidance for parser strategy, but Stage Two catalog lifecycle uses the DB statuses above.

## ParserResult Contract

A parser returns `ParserResult`:

- `events`: list of normalized event rows;
- counters: rows read/parsed/failed, events emitted;
- errors/warnings/metadata;
- optional `status_override`: `EMPTY_FILE`, `FAILED`, `SKIPPED`, `UNSUPPORTED_FORMAT`.

`ParserResult.status_decision` maps the result to parser run/file statuses. Empty output without an explicit reason must not be hidden as a successful benign dataset.

## Errors and Edge Cases

| Scenario | Behavior |
| --- | --- |
| Missing parser class | Seed entry becomes inactive or receives validation diagnostics. |
| Parser not found | `dataset_files.status = UNSUPPORTED_FORMAT`. |
| Large binary PCAP/PCAPNG | Use `--packet-mode packet-summary` or `sample`; account for performance risk. |
| TEST labels in filename | Filename hints are disabled for `TEST`. |
| Mixed schema CSV/JSON | Parser should preserve unknown fields in JSON payloads and emit warnings. |
| Partially corrupt file | `PARTIAL_SUCCESS`/`PARTIALLY_PARSED` is allowed; counters must show failed rows. |

## Coverage Check

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage dns
python manage.py stage-two parser-coverage host
```

The check compares registered `dataset_files` combinations with `parser_registry`. Run it after `catalog-ingest` and `seed-parser-registry`.
