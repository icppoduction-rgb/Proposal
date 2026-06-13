# Stage Two: Data Normalization

Stage Two converts raw dataset files into a reproducible artifact chain:

```text
raw dataset file -> PostgreSQL catalog -> normalized Parquet -> feature Parquet -> model-ready artifacts
```

PostgreSQL stores catalog metadata, statuses, relationships, and reports. Large normalized, feature, and model-ready data stays in Parquet under `PATH_DATA_STORAGE`. DuckDB is used for SQL checks over Parquet.

## Main Commands

```powershell
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two normalize-dns
python manage.py stage-two normalize-host
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Normalization commands process files marked `READY_FOR_PARSING`. An optional limit is supported:

```powershell
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

## Sections

- [Storage architecture](storage_architecture.md)
- [PostgreSQL catalog schema](postgresql_catalog_schema.md)
- [Normalized event schema](normalized_event_schema.md)
- [Parser strategy](parser_strategy.md)
- [Parquet and DuckDB artifacts](parquet_duckdb_artifacts.md)
- [Data quality checks](data_quality_checks.md)
- [Data leakage prevention](data_leakage_prevention.md)

## Core Invariants

- TRAIN, VALIDATION, and TEST are not mixed in catalog rows, Parquet paths, or model-ready artifacts.
- TEST is never used to fit scalers, encoders, imputers, feature selectors, thresholds, or models.
- Missing source fields are stored as `NULL`/Parquet null instead of synthetic values.
- Traceability must preserve model-ready -> feature -> normalized -> parser run -> raw file -> dataset links.
- Labels are separated from X features; leakage columns are forbidden in X.
