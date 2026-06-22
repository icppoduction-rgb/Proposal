# Normalized Event Schema

Schema file: `schemas/normalized/normalized_event_v1.json`.

Registration code: `scripts/stage_two/normalization/schema_contracts.py`.

Catalog table: `schema_versions`.

## Purpose

`normalized_event/v1` defines a unified event-level contract for DNS, host, network, and hybrid sources. Parsers must emit events with required normalized fields. `BaseParser.validate_result()` checks required fields, and the schema JSON fixes the full field list and null policy.

## Required Parser-level Fields

`scripts/stage_two/parsers/base.py` requires:

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

The schema JSON additionally defines nullable/type/allowed values for canonical fields.

## Traceability Fields

| Field | Purpose |
|---|---|
| `event_uid` | stable event identity, usually hash/context/index |
| `dataset_id` | FK-like catalog id, nullable for non-catalog contexts |
| `file_id` | raw dataset file id |
| `dataset_name` | dataset name from catalog/context |
| `dataset_role` | `TRAIN`, `VALIDATION`, `TEST`, `EXPERIMENTS` |
| `branch` | `dns`, `host`, `network`, `hybrid` |
| `source_format` | catalog source format |
| `source_file_path` | relative or absolute raw/sorted source path |
| `source_file_hash` | SHA-256 from catalog |
| `parser_name`, `parser_version` | parser identity |
| `parser_run_id` | parser run catalog id |
| `schema_name`, `schema_version` | normalized schema identity |

These fields support downstream traceability and audits. They must not be included in model-ready X features.

## Timestamp Contract

Fields:

- `timestamp`: nullable UTC timestamp;
- `timestamp_source`: source column/header/packet header/etc.;
- `timestamp_type`: required enum;
- `event_index`: nullable event order index.

Allowed `timestamp_type`:

| Value | Meaning |
|---|---|
| `absolute` | source contains absolute timestamp |
| `relative` | source contains relative timestamp/delta |
| `event_order` | absolute time is absent, but event order is meaningful |
| `missing` | no time and no reliable order timestamp |

Rules:

- `timestamp` can be `null`.
- Missing time must not be replaced with current time.
- `created_at` records normalized row creation time, not event time.
- If timestamp is missing, parser must use `timestamp_type='missing'` or `event_order` and preserve `event_index`.

## DNS Fields

DNS-specific fields:

- `domain`;
- `query_domain`;
- `qtype`;
- `qclass`;
- `ttl`;
- `rcode`;
- network endpoints: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`.

DNS parsers may also store source-specific values in `features_json`, `raw_fields_json`, or `metadata_json`.

## Host Fields

Host-specific fields:

- `host_name`;
- `user_name`;
- `process_id`;
- `process_name`;
- `parent_process_id`;
- `parent_process_name`;
- `syscall_name`;
- `event_id`;
- `command_line`;
- `file_path`;
- metrics: `metric_name`, `metric_value`.

Host parsers may emit modalities such as `host`, `host_metric`, `sandbox`, `host_network_packet`.

## Network/Hybrid Fields

Network/hybrid data uses:

- endpoint fields `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`;
- DNS fields when packet contains DNS;
- `modality` to distinguish packet/flow/DNS/host events;
- `features_json` for derived flow/packet metrics.

## Label Fields

Canonical labels:

| Field | Meaning |
|---|---|
| `label_binary` | `0`, `1`, or null |
| `label_family` | high-level label family, for example benign/malware/dns_exfiltration |
| `label_subtype` | lower-level label subtype |
| `label_source` | `embedded_column`, `filename`, `scenario_metadata`, `external_label_file`, `ids_alert`, `ground_truth_csv`, `none` |
| `label_status` | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label` |
| `label_confidence` | nullable confidence |
| `label_mapping_rule_id` | rule id or source marker |

Unlabeled event contract:

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

Missing label does not mean benign.

## JSON Fields

| Field | Use |
|---|---|
| `features_json` | normalized low-level source features useful before feature extraction |
| `raw_fields_json` | source fields/raw row fragments needed for audit/debug |
| `metadata_json` | parser/source metadata, warnings, schema hints, helper flags |

`ParquetArtifactWriter` serializes columns ending with `_json` into deterministic JSON strings before PyArrow inference.

## Null Policy

Schema JSON explicitly states:

- missing source field -> JSON null / SQL NULL / Parquet null;
- missing labels -> unlabeled fields, not benign;
- missing timestamps -> `timestamp=null`, `timestamp_type=missing`;
- ordered streams should provide `event_index`;
- `TEST` statistics must not be used for fit/tuning/feature selection/model training.
