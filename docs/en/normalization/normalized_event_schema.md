# Normalized Event Schema

The normalized event contract is stored in `schemas/normalized/normalized_event_v1.json`. Stage Two parsers must emit rows compatible with this contract.

## Base Traceability Fields

Required traceability fields:

- `event_uid`
- `dataset_id`
- `file_id`
- `dataset_name`
- `dataset_role`
- `branch`
- `source_format`
- `source_file_path`
- `source_file_hash`
- `parser_name`
- `parser_version`
- `parser_run_id`
- `schema_name`
- `schema_version`
- `created_at`

## Time Model

- `timestamp` may be null.
- `timestamp_type` is one of `absolute`, `relative`, `event_order`, or `missing`.
- If no absolute time exists, ordered streams should preserve `event_index`.
- Missing time must not be replaced with the current time.

## Entity and Modality

The schema covers DNS, host, network, and hybrid events. Common fields include:

- `entity_type`, `entity_id`
- `event_type`, `raw_event_name`, `modality`
- host fields: `host_name`, `user_name`, `process_id`, `process_name`, `file_path`, `command_line`
- network/DNS fields: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `domain`, `query_domain`, `qtype`, `qclass`, `ttl`, `rcode`
- metric fields: `metric_name`, `metric_value`

## Labels

Labels are represented by:

- `label_binary`: `0`, `1`, or null
- `label_family`
- `label_subtype`
- `label_source`
- `label_status`
- `label_confidence`
- `label_mapping_rule_id`

If a label is missing, use:

```text
label_binary = null
label_source = none
label_status = unlabeled
```

The TEST filename heuristic is disabled: TEST labels are not inferred from file names without an explicit safe source.

## Raw and Extra Metadata

Parser-specific source fields and additional metadata use:

- `features_json`
- `raw_fields_json`
- `metadata_json`

Missing fields are stored as null.
