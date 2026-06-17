# Parser Strategy

Stage Two uses a registry-driven parser pipeline:

```text
dataset_files.source_format -> parser_registry -> ParserResolver -> parser class -> ParserResult -> normalized Parquet
```

The parser seed is `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Load or refresh it with:

```powershell
python manage.py stage-two seed-parser-registry
```

## Source Format Detection

`DatasetFileScanner` in `scripts/stage_two/ingestion/scanner.py` detects:

1. `branch` from path/root parts: `dns`, `host`, otherwise `hybrid`.
2. `role` from path parts: `TRAIN`, `VALIDATION`, `TEST`, otherwise `EXPERIMENTS`.
3. `source_format` from sorted-tree format buckets first, then file-name heuristics.

Compound names are preserved. For example:

```text
pcap.csv -> pcap.csv
process.summary.log -> process.summary.log
journal~ -> journal~
netflow_day -> netflow_day
```

## Active Parser Coverage

| Branch | Parser class | Source formats | Role scope |
| --- | --- | --- | --- |
| dns | `DnsCsvParser` | `csv` | all roles |
| dns | `DnsPcapCsvParser` | `pcap.csv` | all roles |
| dns | `DnsTxtDomainListParser` | `txt` | VALIDATION |
| dns | `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` | all roles |
| host | `HostCsvParser` | `csv` | all roles |
| host | `HostJsonLinesParser` | `json`, `json-1` | all roles |
| host | `HostLineLogParser` | `auth.log`, `info`, `journal`, `journal~`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `messages`, `messages-1`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log` | all roles |
| host | `HostLineLogParser` -> `HostMetricbeatParser` | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | all roles |
| host | `HostSyscallTraceParser` | `ghc`, `sc`, `txt` | all roles |
| host | `HostBsonSandboxParser` | `bson` | TEST |
| host | `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` | all roles |
| host | `HostXmlParser` | `xml` | all roles |
| host | `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` | TRAIN, VALIDATION |

The authoritative runtime view is:

```powershell
python manage.py stage-two parser-coverage
```

## ParserResolver

`ParserResolver`:

- selects active rows by `branch`, `role`, `source_format`, and `priority`;
- validates module/class availability before selecting a parser;
- loads parser classes as `BaseParser` subclasses;
- resolves `schema_version_id` from `schema_versions`;
- marks files `UNSUPPORTED_FORMAT` when no parser exists.

Missing classes are reported in parser coverage instead of being hidden runtime exceptions.

## Input Reader Behavior

`UniversalInputReader` supports:

| Mode | Purpose |
| --- | --- |
| `text` | Text stream with encoding fallback. |
| `lines` | Streaming line iteration. |
| `records` | Generic record iteration. |
| `json_lines` | JSON Lines. |
| `csv_rows` | CSV rows. |
| `binary` | Binary content. |
| `packet_bytes` | PCAP/CAP/PCAPNG bytes/chunks. |
| `bson_stream` | BSON document streams. |

Safety behavior:

- UTF-8 BOM detection and fallback through configured text encodings.
- gzip, bz2, xz/lzma, and safe ZIP member handling.
- conservative whole-file, line-level, and JSON payload base64 decoding.
- no raw file mutation.
- no eval/pickle/subprocess execution.
- bounded raw previews and bounded error samples.

## Status Model

| Parser condition | Parser status | File status |
| --- | --- | --- |
| parsed > 0 and failed = 0 | `SUCCESS` | `PARSED` |
| parsed > 0 and failed > 0 | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| no usable content | `EMPTY_FILE` | `EMPTY_FILE` |
| cannot read/parse safely | `FAILED` | `FAILED` |
| intentionally skipped helper file | `SKIPPED` | `SKIPPED` |
| no active parser | `UNSUPPORTED_FORMAT` | `UNSUPPORTED_FORMAT` |

## Labels

Parsers delegate label decisions to `LabelResolver`.

- Embedded labels and mapping rules are allowed only when role-safe.
- TEST filename heuristics are disabled.
- Absence of a label produces explicit unlabeled fields.
- Label and source metadata are excluded from X/model input features by schema contracts and leakage checks.

## Reports

Parser coverage:

```text
PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md
PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md
```

Per-run parser diagnostics:

```text
PATH_DATA_STORAGE/reports/en/stage-two/parser/
PATH_DATA_STORAGE/reports/ru/stage-two/parser/
```

## Adding Parsers

See [Parser development guide](parser_development_guide.md).
