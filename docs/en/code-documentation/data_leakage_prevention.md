# Data Leakage Prevention

Leakage prevention is enforced by documentation, contracts, runtime validation, and DuckDB checks. Conventions alone are not enough.

## Hard Rules

1. `TEST` is never used for training, preprocessing fit, encoder/scaler fit, threshold tuning, or feature selection.
2. `TRAIN`, `VALIDATION`, and `TEST` remain physically partitioned by role in Parquet paths.
3. Labels are stored separately from X features.
4. Model-ready X artifacts must not contain label/source/traceability leakage columns.
5. Missing labels get `unlabeled`, not benign.
6. TEST filename heuristic is disabled.

## Code Enforcement

| Rule | Code |
|---|---|
| X forbidden columns | `scripts/stage_two/model_ready/contracts.py::validate_x_columns` |
| Feature-layer excluded columns | `scripts/stage_two/features/contracts.py::X_EXCLUDED_COLUMNS` |
| TRAIN-only preprocessing | `validate_preprocessing_fit_role()` and DB check constraint |
| TEST filename heuristic disabled | `LabelResolver.label_hints_allowed()` |
| Leakage report | `LeakageChecker` |

## Forbidden X Columns

The current code uses `X_EXCLUDED_COLUMNS`/`X_FORBIDDEN_COLUMNS`. The required forbidden list from the task is covered and extended by implementation:

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

Note: `model_ready_v1.json` currently omits `entity_type`, `entity_id`, `window_start`, `window_end`, `window_size_seconds`, `window_step_seconds`, but `features/contracts.py` includes them in `X_EXCLUDED_COLUMNS`. Use the stricter union for X validation.

## LeakageChecker Checks

Command:

```bash
python manage.py stage-two run-leakage-checks
```

Checks:

| Check | Failure condition |
|---|---|
| `x_forbidden_columns` | forbidden X columns exist in model-ready X files with non-null values |
| `test_absent_from_train` | `dataset_role='TEST'` appears in TRAIN model-ready files |
| `preprocessing_fit_only_train` | preprocessing artifact has `fitted_on_role != 'TRAIN'` |

Failed leakage report severity: `CRITICAL`.

`block_model_ready_if_failed()` can mark a successful model-ready artifact as `BLOCKED` when leakage report failed.

## Safe Model-ready Pattern

Expected artifact separation:

```text
parquet/model_ready/tabular/{branch}/TRAIN/schema=v1/X_train.parquet
parquet/model_ready/labels/{branch}/TRAIN/schema=v1/y_train.parquet
parquet/model_ready/tabular/{branch}/VALIDATION/schema=v1/X_validation.parquet
parquet/model_ready/labels/{branch}/VALIDATION/schema=v1/y_validation.parquet
parquet/model_ready/tabular/{branch}/TEST/schema=v1/X_test.parquet
parquet/model_ready/labels/{branch}/TEST/schema=v1/y_test.parquet
```

X files contain only model features. y files contain labels. Traceability/source fields remain in catalog and optional audit artifacts, not in X.

## Unsafe Assumptions

- Do not infer `benign` from a missing label.
- Do not use filename labels for TEST.
- Do not tune thresholds on TEST.
- Do not mix role partitions into a single X artifact.
- Do not keep `source_file_path`/`event_uid`/`dataset_name` in X because models can memorize source identity.
