# Data Leakage Prevention

Leakage prevention in Stage Two relies on contract-level exclusions, catalog traceability, and runtime checks. The main goal is that labels, source identifiers, and split metadata must not enter model-ready `X`.

## Non-Negotiable Rules

1. `TEST` is not used for training, preprocessing fit, scaler fit, encoder fit, threshold tuning, or feature selection.
2. `TRAIN`, `VALIDATION`, and `TEST` are not mixed in one model-ready artifact.
3. Labels are not ordinary input features.
4. Filename heuristics for `TEST` labels are forbidden.
5. Missing labels do not mean benign.
6. Traceability fields are preserved in catalog/metadata but excluded from `X`.

## Forbidden X Columns

Forbidden columns come from feature/model-ready contracts:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
label
labels
target
class
is_attack
is_malicious
malicious
attack
attack_cat
attack_category
attack_subcat
is_executing_exploit
exploit
ground_truth
ground_truth_label
dataset_id
dataset_name
dataset_role
role
branch
source_format
source_file
source_file_name
source_file_path
source_file_hash
source_normalized_path
source_event_uid_refs
parser_run_id
parser_name
parser_version
schema_name
schema_version
normalized_artifact_id
feature_group
feature_schema_name
feature_schema_version
event_uid
sample_uid
entity_type
entity_id
window_start
window_end
window_size_seconds
window_step_seconds
scenario_name
raw_fields_json
metadata_json
created_at
```

`ModelReadyRegistryService.write_table_artifact()` calls `validate_x_columns()` for `data_type = "X"` and rejects rows containing forbidden fields.

## LeakageChecker

Command:

```bash
python manage.py stage-two run-leakage-checks
```

Code:

```text
scripts/stage_two/quality/checkers.py
```

Checks:

| Check | What it catches |
| --- | --- |
| `x_forbidden_columns` | Label/source/traceability columns inside model-ready `X`. |
| `test_absent_from_train` | `TEST` used in training context. |
| `preprocessing_fit_only_train` | Preprocessing artifact fitted on a role other than `TRAIN`. |

CRITICAL violations are registered in `data_quality_reports` and must block artifact use.

## Labels

Label fields may exist in normalized events for audit and in model-ready `y`, but not in `X`. Events without labels remain unlabeled:

```json
{
  "label_binary": null,
  "label_source": "none",
  "label_status": "unlabeled"
}
```

See [label_resolver.md](label_resolver.md).

## Traceability Without Leakage

Traceability chain is mandatory:

```text
raw -> normalized -> features -> model-ready
```

But traceability identifiers (`event_uid`, `sample_uid`, paths, hashes, parser IDs) must not become features. They must remain in:

- PostgreSQL Catalog;
- artifact metadata;
- non-X columns excluded from the training matrix.

## DNS supervised 70/30 policy

For the DNS supervised split `dns_supervised_70_30_v1`, leakage prevention
includes both X-column exclusion and source exclusion:

- the current DNS `TEST/csv` source and its chunked downstream artifacts are not used in supervised evaluation;
- `ens33-dns_amplification_attack.pcap` is fully excluded;
- `ens33-dns_amplification_attack__f291ed87a1.pcap` is capped by the global target;
- `label_binary=NULL` is excluded, not converted to normal;
- `split_index.parquet` is checked for no `sample_uid` overlap between `TRAIN`, `VALIDATION`, and `TEST`;
- `traceability.parquet` keeps `source_role`, `normalized_artifact_id`, `source_normalized_path`, and `split_policy_id`, but these fields do not enter `X.parquet`.

Training-readiness verdict:

- active experiment: `dns_rebalanced_70_30_v1`;
- status: ready for supervised tabular model training;
- quality checks: `PASS`, no `blocking_issues`, no timestamp warnings;
- leakage/traceability checks: `PASS`;
- `TEST` remains final-evaluation only.

Verification reports:

```text
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task18-stage-three-quality-checks.md
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task19-stage-three-leakage-and-traceability-checks.md
```

## Common Mistakes

| Mistake | Consequence | Fix |
| --- | --- | --- |
| `label_binary` enters X | The model learns the answer. | Rebuild X after applying the exclusion contract. |
| `source_file_path` enters X | The model can learn dataset/source identity. | Remove source fields from feature selection. |
| `TEST` is used for scaler fit | Metrics become inflated. | Fit only on `TRAIN`, transform `VALIDATION`/`TEST`. |
| Unlabeled is replaced with benign | Labels are corrupted. | Keep `label_binary = null`, `label_status = unlabeled`. |
| Filename heuristic for TEST | Leakage from file name. | Disable the heuristic; use only explicit ground truth. |
