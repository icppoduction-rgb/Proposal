# Normalized Event Schema

The canonical normalized event schema is:

```text
schemas/normalized/normalized_event_v1.json
```

It is registered in PostgreSQL `schema_versions` by:

```powershell
python manage.py stage-two seed-parser-registry
```

## Field Groups

| Group | Representative fields | Purpose |
| --- | --- | --- |
| Traceability | `event_uid`, `dataset_id`, `file_id`, `dataset_name`, `dataset_role`, `branch`, `source_format`, `source_file_path`, `source_file_hash`, `parser_name`, `parser_version`, `parser_run_id`, `schema_name`, `schema_version` | Connect every normalized row back to raw file and parser run. |
| Time/order | `timestamp`, `timestamp_source`, `timestamp_type`, `event_index` | Preserve absolute timestamps, relative timestamps, or stream order. |
| Event identity | `entity_type`, `entity_id`, `event_type`, `raw_event_name`, `modality` | Describe the event domain and normalized type. |
| Host | `host_name`, `user_name`, `process_id`, `process_name`, `parent_process_id`, `parent_process_name`, `syscall_name`, `event_id`, `command_line`, `file_path` | Host/syscall/log/sandbox fields. |
| Network/DNS | `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `domain`, `query_domain`, `qtype`, `qclass`, `ttl`, `rcode` | DNS, packet, and flow fields. |
| Metrics | `metric_name`, `metric_value` | Host metricbeat/system metrics. |
| Labels | `label_binary`, `label_family`, `label_subtype`, `label_source`, `label_status`, `label_confidence`, `label_mapping_rule_id` | Canonical label metadata, kept out of X features. |
| Flexible JSON | `features_json`, `raw_fields_json`, `metadata_json` | Non-canonical source fields, parser metadata, bounded previews, derived parser-safe features. |

## Timestamp Policy

| `timestamp_type` | Meaning |
| --- | --- |
| `absolute` | Source provided an absolute timestamp. |
| `relative` | Source provided a relative time/counter. |
| `event_order` | No absolute time; `event_index` preserves order. |
| `missing` | No usable time and no ordered event context. |

Parsers must not inject the current year/timezone silently when the source does not provide enough context.

## Null Policy

- Missing values are stored as JSON null, SQL NULL, or Parquet null.
- Missing labels are not treated as benign.
- Unlabeled events use `label_binary=None`, `label_source="none"`, `label_status="unlabeled"`.
- Unknown source fields should be preserved in JSON fields instead of dropped.

## Required Parser Behavior

Every emitted event must include the required normalized fields defined in `scripts/stage_two/parsers/base.py`. Parser smoke tests validate this through `REQUIRED_NORMALIZED_FIELDS`.

Recommended event creation path:

1. Build traceability fields using helpers from `scripts/stage_two/parsers/common.py`.
2. Add timestamp/order fields.
3. Resolve labels with `LabelResolver`.
4. Merge canonical fields, `raw_fields_json`, `features_json`, and `metadata_json`.
5. Return a `ParserResult` with counters and status.
