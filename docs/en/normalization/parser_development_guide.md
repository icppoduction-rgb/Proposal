# Parser Implementation Development Guide

This document defines the minimum contract for a new Stage Two parser. A new parser must be safe for raw data, must not mix roles, and must preserve traceability.

## Where to Change Code

| Task | File/directory |
| --- | --- |
| Parser class | `scripts/stage_two/parsers/*.py` |
| Shared helpers | `scripts/stage_two/parsers/common.py`, `csv_utils.py`, `json_utils.py`, `input_reader.py` |
| Registry entry | `scripts/stage_two/parser_registry/parser_registry_seed.json` |
| Schema contract | `schemas/normalized/normalized_event_v1.json` or a new schema version |
| Parser tests/smoke | `scripts/stage_two/parser_smoke.py`, `parser_input_smoke.py`, project tests if present |
| Documentation | `docs/en/normalization/parser_strategy.md`, this file, and schema docs when needed |

## Minimum Parser Contract

The parser class must:

1. inherit from `BaseParser`;
2. accept `ParserContext`;
3. return `ParserResult`;
4. fill required normalized fields;
5. never modify the raw file;
6. preserve `event_index` or another ordering signal when timestamp is missing;
7. use `LabelResolver`, not assign benign by default;
8. preserve unknown raw values in `raw_fields_json`/`metadata_json` instead of dropping them.

Required fields are listed in [normalized_event_schema.md](normalized_event_schema.md).

## Implementation Sketch

```python
from pathlib import Path

from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import build_timestamp_fields
from scripts.stage_two.parsers.input_reader import UniversalInputReader


class MyParser(BaseParser):
    parser_name = "my_parser"
    parser_version = "v1"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        events: list[dict[str, object]] = []
        errors: list[str] = []

        reader = UniversalInputReader(path)
        with reader.open("json_lines") as records:
            for event_index, raw_record in enumerate(records):
                try:
                    timestamp_fields = build_timestamp_fields(
                        raw_record.get("timestamp"),
                        event_index=event_index,
                    )
                    labels = self.label_resolver.resolve(raw_record, context)
                    events.append(self.base_event(
                        context,
                        event_index=event_index,
                        **timestamp_fields,
                        **labels,
                        event_type="my_event",
                        entity_type="host",
                        modality="host_event",
                        raw_fields_json=raw_record,
                    ))
                except Exception as exc:
                    errors.append(f"event_index={event_index}: {exc}")

        return ParserResult(
            events=events,
            rows_read=len(events) + len(errors),
            rows_parsed=len(events),
            rows_failed=len(errors),
            error_samples=errors,
        )
```

Use the reader mode that matches the format (`csv_rows`, `json_lines`, `lines`, `binary`, `packet_bytes`, `bson_stream`). Do not add pseudo-fields to normalized output without updating the schema contract.

## Registry Entry

After adding a class, add or extend a parser group in:

```text
scripts/stage_two/parser_registry/parser_registry_seed.json
```

Minimum fields:

```json
{
  "parser_name": "my_parser",
  "parser_version": "v1",
  "branch": "host",
  "source_formats": ["my_format"],
  "supported_roles": null,
  "priority": 100,
  "normalized_schema_name": "normalized_event",
  "normalized_schema_version": "v1",
  "parser_module": "scripts.stage_two.parsers.host",
  "parser_class": "MyParser"
}
```

`supported_roles = null` means all active roles. If the parser is valid only for `TEST` or only for `TRAIN/VALIDATION`, set the list explicitly. For example, `HostBsonSandboxParser` is limited to `TEST`, and `HostPacketCaptureParser` is limited to `TRAIN`/`VALIDATION`.

## Label Handling

The parser must not assign `label_binary = 0` when a label is missing. Use `LabelResolver`:

- explicit embedded/external labels produce `explicit_label` or a configured status;
- weak/inferred labels must include confidence/source;
- conflicting labels must be recorded as `conflicting_label`;
- filename/embedded heuristics are disabled for `TEST`.

See [label_resolver.md](label_resolver.md).

## Timestamp Handling

Do not substitute `datetime.now()` for a missing timestamp.

Rules:

```text
timestamp present -> timestamp_type = absolute
timestamp missing but event_index present -> timestamp_type = event_order
timestamp missing and no ordering -> timestamp_type = missing
```

## Error Handling

| Error | How to record it |
| --- | --- |
| Corrupt row | Increment failed counter, add an error sample, continue if possible. |
| Empty file | Return status override `EMPTY_FILE` or `SKIPPED`; do not create fake benign events. |
| Unsupported subformat | Return `UNSUPPORTED_FORMAT` or error metadata if the parser cannot safely read the file. |
| Schema drift | Preserve raw payload in JSON fields and add a warning. |
| Large binary file | Use packet summary/sample modes; do not load the entire file into memory without need. |

## Checks After Adding a Parser

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --dry-run
python manage.py stage-two normalize-format --branch <branch> --role <ROLE> --format <format> --limit 10
python manage.py stage-two run-duckdb-checks
```

If the parser affects labels or model-ready downstream, also run:

```bash
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

## Documentation to Update

- `parser_strategy.md` - parser classes/source formats.
- `normalized_event_schema.md` - when new normalized fields or a new schema version are added.
- `label_resolver.md` - when new label fields/rules are added.
- `data_quality_checks.md` - when a new quality check is needed.
- `performance_tuning.md` - when the parser requires special runtime limits.
