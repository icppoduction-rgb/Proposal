# Parser Development Guide

This guide describes the supported way to add or modify Stage Two parser implementations.

## Parser Contract

Every parser subclasses `BaseParser` from `scripts/stage_two/parsers/base.py` and returns `ParserResult`.

Core classes:

| Class | Purpose |
| --- | --- |
| `ParserContext` | Traceability input passed to each parser: dataset/file ids, role, branch, source format, source path/hash, parser run id, metadata. |
| `ParsedEvent` | Typed event wrapper used by parser helpers. Parsers may also emit normalized event dictionaries through helpers. |
| `ParserResult` | Parser output: events, counters, warnings, error samples, parser/file statuses. |
| `BaseParser` | Abstract parser base with parser name/version/schema metadata. |

Required normalized fields are defined by `REQUIRED_NORMALIZED_FIELDS` in `base.py` and by `schemas/normalized/normalized_event_v1.json`.

## Use The Shared Helpers

Use existing utilities before adding custom code:

| Utility | File | Use |
| --- | --- | --- |
| `UniversalInputReader` | `scripts/stage_two/parsers/input_reader.py` | Streaming text/CSV/JSON-lines, binary streams, encoding, compression, safe base64. |
| Event builder helpers | `scripts/stage_two/parsers/common.py` | Stable event UID, traceability fields, labels, timestamps, metadata merge. |
| CSV helpers | `scripts/stage_two/parsers/csv_utils.py` | Headered/headerless CSV row handling. |
| JSON helpers | `scripts/stage_two/parsers/json_utils.py` | JSON-line/array/object handling and flattening. |
| Log helpers | `scripts/stage_two/parsers/logs.py` | Syslog/auth/mail/journal line parsing. |
| `LabelResolver` | `scripts/stage_two/labels/resolver.py` | Safe label extraction and label mapping rules. |

## Implementation Steps

1. Add or update parser class in the most specific parser module:

| Format family | Preferred module |
| --- | --- |
| DNS CSV/TXT/pcap.csv | `scripts/stage_two/parsers/dns.py` |
| Host CSV/JSON/log/syscall wrappers | `scripts/stage_two/parsers/host.py` |
| Metricbeat/system metrics | `scripts/stage_two/parsers/metrics.py` |
| NetFlow/WLS | `scripts/stage_two/parsers/netflow.py` |
| Packet captures | `scripts/stage_two/parsers/packet.py` |
| BSON sandbox telemetry | `scripts/stage_two/parsers/bson.py` |
| XML | `scripts/stage_two/parsers/xml.py` |

2. Export the parser from `scripts/stage_two/parsers/__init__.py` if it must be imported by tests or registry validation.
3. Add or update a registry entry in `scripts/stage_two/parser_registry/parser_registry_seed.json`.
4. Ensure scanner inference recognizes the format in `scripts/stage_two/ingestion/scanner.py`.
5. Add direct parser smoke coverage in `scripts/stage_two/parser_smoke.py` and/or focused tests in `tests/stage_two/`.
6. Add encoded/compressed coverage in `scripts/stage_two/parser_input_smoke.py` when relevant.
7. If catalog behavior changes, update `scripts/stage_two/parser_catalog_smoke.py`.
8. Run validation commands.

## Registry Rules

Each registry group needs:

```json
{
  "parser_name": "host_netflow_parser",
  "parser_version": "v1",
  "branch": "host",
  "source_formats": ["netflow_day", "netflow_ids", "wls_day"],
  "supported_roles": null,
  "normalized_schema_name": "normalized_event",
  "normalized_schema_version": "v1",
  "parser_module": "scripts.stage_two.parsers.host",
  "parser_class": "HostNetflowParser",
  "priority": 50,
  "supports_streaming": true,
  "requires_external_tools": false
}
```

Do not set a registry row active for a class that cannot be imported. `ParserResolver` and parser coverage validation will report missing classes.

## Status Rules

Use the shared status model:

| Condition | Parser run status | Dataset file status |
| --- | --- | --- |
| Parsed rows and no failures | `SUCCESS` | `PARSED` |
| Parsed rows and row failures | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| No usable content | `EMPTY_FILE` | `EMPTY_FILE` |
| Parser cannot safely read file | `FAILED` | `FAILED` |
| Helper/context file intentionally skipped | `SKIPPED` | `SKIPPED` |
| No active parser exists | `UNSUPPORTED_FORMAT` | `UNSUPPORTED_FORMAT` |

Do not silently drop unknown rows. Increment `rows_failed` and keep bounded `error_samples`.

## Label Rules

- Use `LabelResolver`; do not implement ad hoc label logic inside parsers.
- Embedded labels are allowed only when role-safe.
- TEST filename heuristics are disabled.
- Missing labels must remain `label_binary=None`, `label_source="none"`, `label_status="unlabeled"`.
- Label fields and traceability fields must not become model input features.

## Raw Data And Payload Safety

- Never modify raw files.
- Do not call `eval`, `pickle`, or subprocesses on decoded content.
- Do not extract ZIP members to filesystem paths.
- Do not store full packet payloads, BSON streams, or full raw logs in `metadata_json` or PostgreSQL.
- Keep previews bounded by `STAGE_TWO_MAX_RAW_PREVIEW_BYTES`.
- Keep base64 decoded bytes under `STAGE_TWO_MAX_BASE64_DECODE_BYTES`.

## Validation Commands

```powershell
python -m compileall manage.py config.py scripts tests
git diff --check
python -m scripts.stage_two.parser_smoke
python -m scripts.stage_two.parser_input_smoke
python -m scripts.stage_two.parser_catalog_smoke
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
```

For DB/catalog changes also run:

```powershell
python -m scripts.db.smoke_check
python -m alembic -c scripts/db/migrations/alembic.ini current
python -m scripts.stage_two.cli_operational_smoke
```

## Common Mistakes

| Mistake | Consequence | Correct approach |
| --- | --- | --- |
| Hardcoding storage paths in parser code | Breaks portability and config control. | Use `config.py` and existing writer/services. |
| Parsing binary files as text | Corrupts packet/BSON handling. | Use binary reader modes. |
| Treating labels as raw model features | Leakage risk. | Keep labels in canonical label fields only. |
| Adding registry entry without class validation | Coverage gaps and runtime failures. | Implement/export class before activation. |
| Marking all files ready without coverage review | Large failed batches. | Run `parser-coverage` first. |
