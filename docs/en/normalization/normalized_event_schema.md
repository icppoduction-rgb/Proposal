# Normalized Event Schema

The normalized event schema is stored at:

```text
schemas/normalized/normalized_event_v1.json
```

It is a JSON contract with `schema_name = "normalized_event"`, `schema_version = "v1"`, `layer = "normalized"`, and a `fields` array. Parser implementations must emit rows compatible with this contract.

## Required Parser Output Fields

The base parser contract in `scripts/stage_two/parsers/base.py` requires:

```text
event_uid
dataset_name
dataset_role
branch
source_format
source_file_path
parser_name
parser_version
schema_name
schema_version
timestamp_type
entity_type
event_type
modality
label_source
label_status
created_at
```

Additional fields from the JSON schema may be nullable, but the parser must preserve traceability and the label/timestamp null policy.

## Traceability Fields

| Field | Purpose |
| --- | --- |
| `event_uid` | Unique normalized event identifier. |
| `dataset_name` | Dataset name from catalog/source context. |
| `dataset_role` | `TRAIN`, `VALIDATION`, or `TEST`. |
| `branch` | `dns`, `host`, `network`, `hybrid`. |
| `source_format` | Raw file format. |
| `source_file_path` | Path to the source file. |
| `source_file_hash` | SHA-256 of the raw file, when available from catalog. |
| `parser_run_id` | Parser run ID, linking the event to `parser_runs`. |
| `parser_name`, `parser_version` | Parser implementation and version. |
| `schema_name`, `schema_version` | Normalized schema version. |
| `event_index` | Event order inside the file, when available. |

Traceability fields must not be removed from normalized artifacts. For model-ready `X`, they are leakage/source columns and must be excluded from features.

## Timestamp Policy

| Field | Rule |
| --- | --- |
| `timestamp` | May be `null`. |
| `timestamp_type` | One of `absolute`, `relative`, `event_order`, `missing`. |
| `event_index` | Preserves order when absolute time is missing. |

If a timestamp is missing, current time must not be substituted. Correct outputs are:

- `timestamp = null`, `timestamp_type = "event_order"` when reliable `event_index` exists;
- `timestamp = null`, `timestamp_type = "missing"` when neither time nor order is available.

`build_timestamp_fields()` in `scripts/stage_two/parsers/common.py` implements this rule: timestamp gives `absolute`, event index without timestamp gives `event_order`, and absence of both gives `missing`.

## DNS Fields

DNS parsers fill DNS/network context fields when present in the source:

- `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`;
- `query_domain`, `qtype`, `qclass`, `rcode`, `ttl`;
- DNS-specific values inside `features_json` or `raw_fields_json` when the source schema does not map directly to normalized fields.

DNS packet captures may emit summary-level events depending on `--packet-mode`.

## Host Fields

Host parsers use host telemetry fields:

- process: `process_id`, `process_name`, parent process fields;
- file/path: `path`, file action fields;
- syscall/log: `sys_call`, `event_id`, `event_type`;
- metrics/log payload when the source format is log-like or metricbeat-like.

For non-standard line logs, some values are preserved in `raw_fields_json`; normalized columns are filled only when values can be extracted without inventing data.

## Network/Hybrid Fields

`network` and `hybrid` branches exist in schema/catalog constants, but the current normalization runner supports only `dns` and `host`. Network/hybrid fields may be used by future parser contracts, but they must not be documented as a fully implemented normalization pipeline.

## Labels

An unlabeled event must have:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Missing labels do not mean benign. For `TEST`, filename/embedded heuristics are disabled by `LabelResolver.label_hints_allowed()` to avoid leakage through filenames or fields that are not explicit external ground truth.

## JSON Fields

| Field | Purpose |
| --- | --- |
| `features_json` | Parser-level extracted attributes that are not yet model-ready X features. |
| `raw_fields_json` | Source fields or raw record fragments for audit/debug. |
| `metadata_json` | Parser/file metadata, warnings, confidence, additional counters. |

`ParquetArtifactWriter` serializes fields ending in `_json` to deterministic JSON strings before writing Parquet.

## Edge Cases

| Scenario | Expected behavior |
| --- | --- |
| Empty file | Parser result may lead to `EMPTY_FILE`/`SKIPPED`; an artifact is not required. |
| Partially corrupted rows | `PARTIAL_SUCCESS`/`PARTIALLY_PARSED` is allowed; errors are stored in parser run counters/error samples. |
| Unknown source format | File receives `UNSUPPORTED_FORMAT` when resolver cannot find a parser. |
| Schema drift | Parser should preserve unknown raw values in `raw_fields_json`/`metadata_json`, not extend model-ready X without schema review. |
