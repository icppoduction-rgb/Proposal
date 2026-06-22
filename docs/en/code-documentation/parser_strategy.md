# Parser Strategy

Parser strategy consists of seed JSON, PostgreSQL `parser_registry`, `ParserResolver`, concrete parser classes, and parser status contracts.

## Registry Seed

Seed file: `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Seed command:

```bash
python manage.py stage-two seed-parser-registry
```

Each parser group defines:

| Field | Meaning |
|---|---|
| `parser_name` | logical parser id |
| `parser_version` | parser version |
| `branch` | `dns` or `host` in the current seed |
| `source_formats` | one or more source format buckets |
| `supported_roles` | null for all roles or explicit roles |
| `normalized_schema_name/version` | target normalized schema |
| `parser_module` | Python module |
| `parser_class` | class name |
| `priority` | lower value wins |
| `supports_streaming` | registry metadata |
| `requires_external_tools` | registry metadata |

Seed validation imports the class and checks `issubclass(BaseParser)`. Missing classes are stored as inactive rows with diagnostics.

## Resolver

File: `scripts/stage_two/parser_registry/resolver.py`.

Resolution query:

```text
branch == dataset_file.branch
source_format == dataset_file.source_format
is_active == true
supported_role == dataset_file.role OR supported_role IS NULL
ORDER BY priority, id
```

If no parser is found, the file is marked `UNSUPPORTED_FORMAT`.

## Base Parser Contract

File: `scripts/stage_two/parsers/base.py`.

Concrete parser must implement:

```python
class MyParser(BaseParser):
    parser_name = "..."
    parser_version = "v1"

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        ...
```

Streaming parsers should override `parse_batches()`.

`ParserContext` carries catalog metadata:

```text
dataset_id, file_id, dataset_name, dataset_role, branch, source_format,
source_file_path, source_file_hash, parser_run_id, metadata
```

`ParserResult` carries counters, events, warnings, bytes read, error samples, and optional status override.

## Status Mapping

| Parser condition | Parser status | `parser_runs.status` | `dataset_files.status` |
|---|---|---|---|
| parsed rows, no failures | `SUCCESS` | `SUCCESS` | `PARSED` |
| parsed rows + failed rows | `PARTIAL_SUCCESS` | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| no rows parsed | `FAILED` | `FAILED` | `FAILED` |
| read failed | `FAILED` | `FAILED` | `FAILED` |
| empty file | `EMPTY_FILE` | `SKIPPED` | `EMPTY_FILE` |
| unsupported format | `UNSUPPORTED_FORMAT` | `SKIPPED` | `UNSUPPORTED_FORMAT` |
| intentionally skipped | `SKIPPED` | `SKIPPED` | `SKIPPED` |

The task wording mentions `PARTIALLY_PARSED`; in current code this is the file status, while parser run status is `PARTIAL_SUCCESS`.

## DNS Parser Classes

| Class | Module | Source formats | Notes |
|---|---|---|---|
| `DnsCsvParser` | `scripts.stage_two.parsers.dns` | `csv` | schema-aware DNS CSV, supports headerless TEST CSV |
| `DnsPcapCsvParser` | `scripts.stage_two.parsers.dns` | `pcap.csv` | extends DNS CSV handling for packet-derived CSV |
| `DnsTxtDomainListParser` | `scripts.stage_two.parsers.dns` | `txt` for `VALIDATION` | domain list parser |
| `DnsPacketCaptureParser` | `scripts.stage_two.parsers.packet` | `cap`, `pcap`, `pcapng` | packet summary parser, DNS modality for DNS packets |

## Host Parser Classes

| Class | Module | Source formats | Notes |
|---|---|---|---|
| `HostCsvParser` | `scripts.stage_two.parsers.host` | `csv` | host CSV/event/metadata tables |
| `HostJsonLinesParser` | `scripts.stage_two.parsers.host` | `json`, `json-1` | JSON lines, arrays, objects, mixed telemetry |
| `HostLineLogParser` | `scripts.stage_two.parsers.host` | many `*.log`, rotated logs, `messages`, `syslog`, `mainlog` | line-oriented log parser |
| `HostSyscallTraceParser` | `scripts.stage_two.parsers.host` | `txt`, `sc`, `ghc` | syscall/API traces |
| `HostPacketCaptureParser` | `scripts.stage_two.parsers.packet` | `cap`, `pcap`, `pcapng` for `TRAIN`, `VALIDATION` | host network packet summaries |
| `HostBsonSandboxParser` | `scripts.stage_two.parsers.bson` | `bson` for `TEST` | BSON sandbox process/API telemetry |

Additional implemented and seeded classes:

| Class | Module | Source formats |
|---|---|---|
| `HostXmlParser` | `scripts.stage_two.parsers.host` via import from `xml.py` | `xml` |
| `HostNetflowParser` | `scripts.stage_two.parsers.host` via import from `netflow.py` | `netflow_day`, `netflow_ids`, `wls_day` |

Implemented but not directly included in the current seed:

| Class | Module | Notes |
|---|---|---|
| `HostMetricbeatParser` | `scripts.stage_two.parsers.metrics` | used/imported for Metricbeat-like telemetry support |

## Unsupported Formats

An unsupported format means there is no active parser registry row for `(branch, role, source_format)`.

Handling:

1. `ParserResolver.resolve_or_mark_unsupported()` sets `dataset_files.status='UNSUPPORTED_FORMAT'`.
2. `normalize-format` returns `UNSUPPORTED_FORMAT` when selected files have no parser.
3. Parser coverage report shows gaps.

## Error Handling

- Per-row parse errors increment `rows_failed` and store bounded error samples.
- Parser exceptions set `parser_runs.status='FAILED'` and `dataset_files.status='FAILED'`.
- `save_parser_run_reports()` writes parser diagnostics.
- `STAGE_TWO_MAX_ERROR_SAMPLES` limits error samples.

## Parser Extension Checklist

1. Add parser class under `scripts/stage_two/parsers`.
2. Inherit `BaseParser`.
3. Emit events through `base_event()`.
4. Preserve `timestamp_type`, `event_index`, labels, and traceability fields.
5. Add parser registry seed entry.
6. Run parser tests and `python manage.py stage-two seed-parser-registry`.
7. Run `python manage.py stage-two parser-coverage <branch>`.
