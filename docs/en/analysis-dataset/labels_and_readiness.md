# Labels and readiness

This document merges label availability and parser/feature readiness information from the old `dataset_labels_availability_and_recommendations.md` and the per-format reports.

## Main rules

1. A missing label does not mean benign.
2. `TEST` must not be used for training, fit preprocessing, feature selection, or threshold tuning.
3. Labels from filename, directory, scenario metadata, or IDS alert must have `label_source`, `label_status`, confidence, and traceability.
4. Weak labels are not ground truth.
5. Files without labels must keep `label_binary = null`, `label_source = none`, `label_status = unlabeled`.
6. Label/source fields must not enter model-ready `X`.

## Canonical label fields

| Field | Purpose |
| --- | --- |
| `label_binary` | `0=benign`, `1=malicious/attack/exfiltration`, `null=unknown`. |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, unknown. |
| `label_subtype` | subtype/scenario, if available. |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none. |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label. |
| `label_confidence` | 1.0 for explicit labels, lower for inferred/weak labels, null/0 for unlabeled. |
| `label_mapping_rule_id` | Mapping rule ID. |
| `dataset_role` | TRAIN / VALIDATION / TEST. |
| `source_file` | Original path/file name. |
| `source_event_id` | Row/packet/event identifier, if applicable. |

## Label availability summary

| Category | Format buckets | Sources |
| --- | ---: | --- |
| Direct labels | 5 | Host TRAIN `cpu.log`, Host TRAIN `csv`, Host TRAIN `json`, Host VALIDATION `csv`, Host TEST `csv` through label CSV. |
| Partial labels / class hints | 6 | DNS TRAIN `csv`/`pcap`/`pcap.csv`, DNS VALIDATION `pcap`/`txt`, DNS TEST `csv`. |
| No embedded labels | 55 | Most host telemetry/log/packet/sequence formats. |

## Sources with direct labels

| Domain | Role | Format | Files | Label field/source | Values | How to use |
| --- | --- | ---: | ---: | --- | --- | --- |
| Host | `TRAIN` | `cpu.log` | 13 | `labels` annotation rows | `crack_passwords`, `escalate` | Partial/weak labels; join to metric windows by timestamp/host. |
| Host | `TRAIN` | `csv` | 101 | columns 7/8/9 | normal/attack categories + binary 0/1 | Main supervised TRAIN source after schema-aware normalization. |
| Host | `TRAIN` | `json` | 219 | `exploit` / `container.role` / `alert` | True/False/normal/victim/alert-derived | Schema-dependent; `exploit` is inferred, `alert` is weak, `container.role` is context. |
| Host | `VALIDATION` | `csv` | 6 | `is_executing_exploit` | False 5813, True 187 | Main validation label/context source. |
| Host | `TEST` | `csv` | 3 | external label CSV | scan/attack labels | Final evaluation only; not training. |

## Sources with filename/class hints

| Domain | Role | Format | Files | Hint values | Limitation |
| --- | --- | --- | ---: | --- | --- |
| DNS | `TRAIN` | `csv` | 8 | benign, malware, phishing, spam | Use as inferred labels only through a fixed mapping. |
| DNS | `TRAIN` | `pcap` | 4 | benign, malware, phishing, spam | Requires packet parser and filename mapping. |
| DNS | `TRAIN` | `pcap.csv` | 14 | audio, benign, compressed, exe, image, text, video | Payload class is not an attack label without a target policy. |
| DNS | `VALIDATION` | `pcap` | 5 | attack, benign | Filename mapping is acceptable for validation after audit. |
| DNS | `VALIDATION` | `txt` | 3 | unknown, benign | `unknown` must not be automatically treated as benign/attack. |
| DNS | `TEST` | `csv` | 1 | boolean-like `label_or_flag` | TEST is evaluation-only; requires a schema policy. |

## Readiness statuses

| Status | Meaning for Stage Two |
| --- | --- |
| `READY_FOR_FEATURE_EXTRACTION` | Can be connected to feature extraction after correct normalization; does not imply labels are present. |
| `NEEDS_CUSTOM_PARSER` | Requires a specialized parser/decoder or binary/schema-aware layer. |
| `PARTIALLY_SUPPORTED` | Partly usable; the parser must distinguish sub-schemas, service files, or fixed schemas. |
| `BROKEN_OR_EMPTY` | Bucket is empty or missing; feature extraction is impossible until the input is restored. |

## Rules for TRAIN / VALIDATION / TEST

| Role | Allowed | Forbidden |
| --- | --- | --- |
| `TRAIN` | Training and fit preprocessing only after label-safe mapping. | Treating weak labels as ground truth without status/confidence. |
| `VALIDATION` | Quality checks and threshold tuning only if the experiment design allows it. | Mixing with TRAIN artifacts. |
| `TEST` | Final evaluation/inference only. | Training, fit scaler/encoder, feature selection, threshold tuning, filename heuristic label inference. |

## Minimal LabelResolver algorithm

1. Save inventory: domain, role, format, source_file, checksum, file_size.
2. During parsing, extract timestamp, host, ip, process/session/scenario identifiers, and row/event/packet id.
3. Apply rules in this order:
   - embedded column;
   - external label file (`ground_truth.csv`, `runs.csv`, attack labels);
   - filename/class hint;
   - scenario metadata;
   - IDS alert as weak label;
   - no match -> unlabeled.
4. On conflict, set `conflicting_label` instead of choosing a class arbitrarily.
5. For `TEST`, allow labels only for evaluation after the training pipeline is complete.

## Relation to normalization

See also:

- [../normalization/label_resolver.md](../normalization/label_resolver.md)
- [../normalization/data_leakage_prevention.md](../normalization/data_leakage_prevention.md)
- [../normalization/traceability.md](../normalization/traceability.md)
