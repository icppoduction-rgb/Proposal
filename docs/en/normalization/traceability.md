# Traceability and Lineage

Traceability links a model-ready artifact back to the source raw file through PostgreSQL Catalog and Parquet metadata. The chain is required for audit, reproducibility, leakage investigation, and verification that raw files were not modified.

## Implementation

Code:

```text
scripts/stage_two/traceability/service.py
```

CLI:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

A numeric argument is resolved as `model_ready_artifacts.id`; a string is resolved as `model_ready_artifacts.artifact_path`.

## Required Chain

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

If a link is missing, `TraceabilityService` raises `TraceabilityError`. Readiness check treats this as `FAILED`.

## Service Output

The trace chain includes metadata blocks:

- `model_ready_artifact`;
- `feature_artifact`;
- `normalized_artifact`;
- `parser_run`;
- `dataset_file`;
- `dataset`.

This is enough to answer:

- which raw file produced the artifact;
- which parser and schema version processed it;
- where the normalized Parquet file is stored;
- which feature artifact was used to create the model-ready artifact;
- which role/branch was used at every layer.

## Traceability Rules

1. `normalized_artifacts.parser_run_id` must reference a real `parser_runs.id`.
2. `parser_runs.file_id` must reference `dataset_files.id`.
3. `feature_artifacts.normalized_artifact_id` must be populated for production artifacts.
4. `model_ready_artifacts.feature_artifact_id` must be populated for traceable model-ready artifacts.
5. Raw file hash in `dataset_files.file_hash_sha256` must match the current file during readiness check.

## Traceability and Leakage

Traceability fields must not be removed from catalog, but they must not be included in model-ready `X`. Paths, hashes, IDs, and raw metadata can identify dataset/source and create leakage. They must remain in catalog/metadata or be excluded through `x_excluded_columns`.

## Verification

```bash
python manage.py stage-two trace-artifact 123
python -m scripts.stage_two.readiness_check
```

`readiness_check` additionally checks one latest traceable model-ready artifact and raw file hashes.
