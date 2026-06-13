# Parquet and DuckDB Artifacts

The Parquet writer is implemented in `scripts/stage_two/parquet/writer.py`. It uses Zstandard compression (`zstd`) by default. After each write it records row count, file size, and SHA-256 content hash.

## Artifact Layers

Normalized:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Features:

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Model-ready:

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

## Feature Artifact Contract

The contract is in `schemas/features/feature_artifact_v1.json`. Implemented feature groups:

- `dns_features`
- `host_syscall_features`
- `host_eventlog_features`
- `host_metrics_features`
- `network_flow_features`
- `hybrid_features`
- `sequence_features`

The feature writer excludes leakage/source/label columns from `feature_count`.

## Model-ready Contract

The contract is in `schemas/model_ready/model_ready_v1.json`. Supported data types are `X`, `y`, `sequence`, `split_index`, and `preprocessing_metadata`.

For `X`, label/source/traceability columns are forbidden. Validation runs before writing model-ready table artifacts.

## DuckDB Analytics

DuckDB logic is implemented in `scripts/stage_two/duckdb/service.py`. Command:

```powershell
python manage.py stage-two run-duckdb-checks
```

It creates views:

- `normalized_all`
- `features_all`
- `model_ready_all`

Views read Parquet through `read_parquet(..., union_by_name=true, filename=true)`. If no files exist, an empty compatible view is created so checks do not fail on empty storage.

Checks include row counts, required columns, split contamination, and schema mismatch. Results are saved to reports and registered in `data_quality_reports`.
