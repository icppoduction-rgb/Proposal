# Stage Two: Data Normalization

Stage Two converts raw dataset files into a reproducible artifact chain:

```text
raw dataset file -> PostgreSQL catalog -> normalized Parquet -> feature Parquet -> model-ready artifacts
```

PostgreSQL stores catalog metadata, statuses, relationships, parser runs, artifact records, and reports. Large normalized, feature, and model-ready data stays in Parquet under `PATH_DATA_STORAGE`. DuckDB is used for SQL checks over Parquet.

## Main Commands

```powershell
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage host
python manage.py stage-two parser-coverage dns
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Parser Workflow

Inspect coverage before changing file statuses:

```powershell
python manage.py stage-two parser-coverage
```

Mark files as ready. Dry-run is the default safety mode; writes require `--apply`:

```powershell
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
```

Normalize a single format:

```powershell
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-format --branch dns --role VALIDATION --format pcap --limit 100
```

Normalize all ready files in one branch by controlled role/format batches:

```powershell
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two normalize-all --branch dns --limit 1000
```

Backward-compatible aliases remain available:

```powershell
python manage.py stage-two normalize-host 10
python manage.py stage-two normalize-dns 10
```

Fallback argument forms are also supported:

```powershell
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
python manage.py stage-two normalize-all host:1000
```

## Generated Parser Reports

Parser coverage reports are written to:

- `PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md`
- `PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md`

Per-run parser and normalization diagnostics are written under:

- `PATH_DATA_STORAGE/reports/en/stage-two/parser/`
- `PATH_DATA_STORAGE/reports/ru/stage-two/parser/`
- `PATH_DATA_STORAGE/reports/en/stage-two/normalization/`
- `PATH_DATA_STORAGE/reports/ru/stage-two/normalization/`

## Sections

- [Storage architecture](storage_architecture.md)
- [PostgreSQL catalog schema](postgresql_catalog_schema.md)
- [Normalized event schema](normalized_event_schema.md)
- [Parser strategy](parser_strategy.md)
- [Final Codex summary template](final_summary_template.md)
- [Parquet and DuckDB artifacts](parquet_duckdb_artifacts.md)
- [Data quality checks](data_quality_checks.md)
- [Data leakage prevention](data_leakage_prevention.md)

## Core Invariants

- TRAIN, VALIDATION, and TEST are not mixed in catalog rows, Parquet paths, or model-ready artifacts.
- TEST is never used to fit scalers, encoders, imputers, feature selectors, thresholds, or models.
- `catalog-ingest` does not automatically mark files as `READY_FOR_PARSING`; `mark-ready` is the explicit operational gate.
- Normalization processes only `READY_FOR_PARSING` files unless a command explicitly documents another behavior.
- Missing source fields are stored as `NULL`/Parquet null instead of synthetic values.
- Traceability must preserve model-ready -> feature -> normalized -> parser run -> raw file -> dataset links.
- Labels are separated from X features; leakage columns are forbidden in X.
