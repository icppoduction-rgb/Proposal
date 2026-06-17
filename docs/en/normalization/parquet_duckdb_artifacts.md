# Parquet And DuckDB Artifacts

Stage Two writes large normalized data to Parquet and uses DuckDB to run SQL checks over Parquet outputs.

## Parquet Writer

Implementation:

```text
scripts/stage_two/parquet/writer.py
```

Main methods:

| Method | Purpose |
| --- | --- |
| `write_normalized()` | Writes normalized event rows to a partitioned Parquet file. |
| `register_normalized_artifact()` | Registers the Parquet output in PostgreSQL `normalized_artifacts`. |

Parquet path template:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

The writer computes artifact metadata such as row count, relative path, and content hash.

## DuckDB Analytics

Implementation:

```text
scripts/stage_two/duckdb/service.py
scripts/stage_two/duckdb/sql/create_views.sql
```

Command:

```powershell
python manage.py stage-two run-duckdb-checks
```

The service creates or refreshes views over normalized, feature, and model-ready Parquet locations. Empty views are created with required columns so downstream checks can run even when a bucket has no rows.

## Quality Report Registration

DuckDB check output is registered through `DataQualityRepository` into `data_quality_reports` and written under:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/
```

Current command output includes:

```text
service: stage-two run-duckdb-checks
status: SUCCESS | FAILED
report_path: reports/en/stage-two/quality/duckdb_analytics_report.json
check_count: <number>
catalog_report_id: <id>
```

## Feature And Model-Ready Contracts

The repository contains contracts for later pipeline stages:

```text
schemas/features/feature_artifact_v1.json
schemas/model_ready/model_ready_v1.json
scripts/stage_two/features/
scripts/stage_two/model_ready/
```

These contracts define traceability, forbidden leakage columns, and expected artifact paths. The current Stage Two operational CLI focuses on catalog ingestion, parser normalization, and checks; it does not expose a full-corpus production feature/model-ready build command.
