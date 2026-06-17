# Parser Strategy

Stage Two normalizes files through a catalog-driven parser layer:

```text
dataset_files.source_format -> parser_registry -> ParserResolver -> parser class -> normalized Parquet
```

The registry seed is stored in `scripts/stage_two/parser_registry/parser_registry_seed.json` and is loaded with:

```powershell
python manage.py stage-two seed-parser-registry
```

`ParserResolver` selects an active parser by `branch`, `source_format`, optional `supported_roles`, and `priority`. Normalization services resolve parser classes through the resolver and register `parser_runs` plus `normalized_artifacts` for each processed file.

## Operational Flow

1. `catalog-ingest` registers files in PostgreSQL and records `branch`, `role`, `source_format`, path, size, and content hash.
2. `parser-coverage` compares catalog formats with active registry entries and writes RU/EN coverage reports.
3. `mark-ready` promotes only allowed statuses to `READY_FOR_PARSING`.
4. `normalize-format` processes one `branch`/`role`/`source_format` slice.
5. `normalize-all` processes all ready files for one branch by role and format, without mixing roles in one uncontrolled batch.

## Parser Coverage

| Branch | Source format | Role coverage | Parser class | Notes |
| --- | --- | --- | --- | --- |
| dns | `csv` | TRAIN, VALIDATION, TEST | `DnsCsvParser` | Domain lists, headered feature CSV, PhishTank-like rows, and DNS TEST 22-column headerless rows. |
| dns | `pcap.csv` | TRAIN, VALIDATION, TEST | `DnsPcapCsvParser` | Packet-derived CSV with DNS/network fields. |
| dns | `txt` | VALIDATION | `DnsTxtDomainListParser` | One-domain-per-line validation/domain-list files. |
| dns | `cap`, `pcap`, `pcapng` | TRAIN, VALIDATION, TEST | `DnsPacketCaptureParser` | Summary-level packet extraction; no full payload storage. |
| host | `csv` | TRAIN, VALIDATION, TEST | `HostCsvParser` | ADFA-like rows, headerless CSV, runs-like metadata, and safe helper-file handling. |
| host | `json`, `json-1` | TRAIN, VALIDATION, TEST | `HostJsonLinesParser` | JSON Lines, JSON arrays, single objects, ECS/Filebeat/Metricbeat-like nested records. |
| host | `auth.log`, `info`, `journal`, `journal~`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `messages`, `messages-1`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log` | TRAIN, VALIDATION, TEST | `HostLineLogParser` | Syslog/auth/mail/journal/raw line logs, including mixed JSON-lines. |
| host | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | TRAIN, VALIDATION, TEST | `HostLineLogParser` -> `HostMetricbeatParser` | Metric formats stay registry-compatible as line logs and are delegated internally to the metric parser. |
| host | `ghc`, `sc`, `txt` | TRAIN, VALIDATION, TEST | `HostSyscallTraceParser` | Syscall/API/trace-like ordered line streams. |
| host | `bson` | TEST | `HostBsonSandboxParser` | BSON sandbox telemetry document streams. |
| host | `netflow_day`, `netflow_ids`, `wls_day` | TRAIN, VALIDATION, TEST | `HostNetflowParser` | Delimited, whitespace, CSV-like, or JSON-line network flow and WLS rows. |
| host | `xml` | TRAIN, VALIDATION, TEST | `HostXmlParser` | Safe event-like XML without DTD or external entity resolution. |
| host | `cap`, `pcap`, `pcapng` | TRAIN, VALIDATION | `HostPacketCaptureParser` | Summary-level host/network packet extraction. |

The generated coverage matrix is written to:

- `PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md`
- `PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md`

## Input Reader Behavior

`UniversalInputReader` is the shared read layer for parsers.

- Text, lines, CSV rows, JSON Lines, and record modes stream data where possible.
- Binary modes for PCAP/CAP/PCAPNG/BSON do not decode bytes as text.
- Encoding detection supports UTF-8 BOM and a fallback chain including `utf-8`, `utf-8-sig`, `cp1252`, `latin-1`, and `ascii`; unrecoverable text errors are recorded as warnings.
- Compression detection supports gzip, bz2, xz/lzma, and safe in-memory ZIP member extraction without archive path traversal.
- Base64 handling is conservative: whole-file, line-level, and JSON payload values are decoded only when validation succeeds, decoded size stays under `STAGE_TWO_MAX_BASE64_DECODE_BYTES`, and decoded bytes look like known text, structured data, or supported binary containers.
- Reader metadata records encoding, compression, base64, decode strategy, bytes read, warnings, and errors without storing full raw payloads.

## Status And Error Behavior

| Status | Meaning |
| --- | --- |
| `SUCCESS` | At least one row/event parsed and no row-level failures were recorded. |
| `PARTIAL_SUCCESS` / `PARTIALLY_PARSED` | At least one row/event parsed and at least one row failed. |
| `EMPTY_FILE` | The input has no usable content. |
| `FAILED` | The parser cannot read or parse the file safely. |
| `SKIPPED` | A helper/context file was intentionally skipped or emitted only safe metadata. |
| `UNSUPPORTED_FORMAT` | No active parser is available for the cataloged format. |

Counters include `rows_read`, `rows_parsed`, `rows_failed`, `bytes_read`, `files_read`, `warnings_count`, and `parse_errors_count`. Error samples are limited by `STAGE_TWO_MAX_ERROR_SAMPLES`.

## CLI Examples

Coverage:

```powershell
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage host
python manage.py stage-two parser-coverage dns
```

Mark files ready. Dry-run is the default safety mode; `--apply` is required for writes:

```powershell
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
```

Normalize one selected format:

```powershell
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-format --branch dns --role VALIDATION --format pcap --limit 100
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
```

Normalize a branch in controlled role/format batches:

```powershell
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two normalize-all --branch dns --limit 1000
python manage.py stage-two normalize-all host:1000
```

Backward-compatible aliases remain available:

```powershell
python manage.py stage-two normalize-host 10
python manage.py stage-two normalize-dns 10
```

## Label Safety

Parsers use `LabelResolver` and keep label fields out of model input features.

- Role-safe embedded labels and configured `label_mapping_rules` are allowed.
- TEST filename heuristics are disabled.
- Missing labels remain `label_binary=None` and `label_status=unlabeled`.
- Source path, dataset role, scenario name, parser metadata, and file metadata remain traceability/context only.

## Known Limitations

- `catalog-ingest` does not automatically promote files to `READY_FOR_PARSING`; use `mark-ready` after reviewing coverage.
- Host packet capture registry entries are active for TRAIN and VALIDATION only. TEST activation requires an explicit label and leakage policy decision.
- BSON sandbox parsing is active for TEST only.
- Packet parsers extract summary fields and lightweight DNS details only; full packet payloads are not stored in PostgreSQL, reports, or metadata JSON.
- The coverage report files reflect the latest `parser-coverage` invocation, including any branch filter used for that run.
