# Data Leakage Prevention

Stage Two protects TRAIN/VALIDATION/TEST splits through storage paths, catalog constraints, schema contracts, and quality checks.

## Core Rules

- TRAIN, VALIDATION, and TEST remain physically separated in Parquet paths.
- TEST is not used to fit preprocessing artifacts.
- X artifacts must not contain labels, source paths, raw metadata, or traceability columns.
- y artifacts store labels separately from X.
- LabelResolver does not apply filename heuristics to TEST.

## TRAIN-only Preprocessing

`preprocessing_artifacts.fitted_on_role` is constrained to `TRAIN` at the PostgreSQL level and by Python validation. The model-ready registry also calls `validate_preprocessing_fit_role`.

## Forbidden X Columns

`schemas/model_ready/model_ready_v1.json` and `scripts/stage_two/model_ready/contracts.py` forbid these columns in X:

- label columns: `label_binary`, `label_family`, `label_subtype`, `label_source`, `label_status`, `label_confidence`;
- split/source columns: `dataset_name`, `dataset_role`, `role`, `branch`, `source_file_path`, `source_file_hash`;
- traceability columns: `source_normalized_path`, `source_event_uid_refs`, `parser_run_id`, `normalized_artifact_id`, `event_uid`, `sample_uid`;
- raw metadata columns: `scenario_name`, `raw_fields_json`, `metadata_json`, `created_at`.

## LeakageChecker

Command:

```powershell
python manage.py stage-two run-leakage-checks
```

Checks:

- forbidden X columns in model-ready Parquet;
- TEST rows are absent from TRAIN model-ready artifacts;
- preprocessing artifacts are fitted only on TRAIN.

If leakage checks fail, report severity becomes `CRITICAL`. `block_model_ready_if_failed` can move a successful model-ready artifact to `BLOCKED`.

## Traceability Without Leakage

Traceability metadata is stored in the catalog for audit, but must not be present in X. Analyze a chain with:

```powershell
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```
