# Stage Two Usage Guide

This runbook describes the implemented operational path from the filtered dataset root to normalized Parquet artifacts.

## Prerequisites

1. Configure `.env` or the process environment:

```text
PATH_DATA_STORAGE=<absolute storage root>
PATH_FOLDER_DATASETS=<absolute raw dataset root retained for Stage One/audit>
PATH_FOLDER_DATASETS_FILTER=<absolute filtered dataset root used by Stage Two>
DATABASE_URL=<PostgreSQL SQLAlchemy URL>
```

2. PostgreSQL must be reachable from `DATABASE_URL`.
3. Python 3.11.x is the supported runtime. On the local Windows dev machine, use `C:\Users\fmark\.conda\envs\proposal2\python.exe` or activate `conda activate proposal2`.
4. Python dependencies from `requirements-dev.txt` must be installed for development and CI checks; production/runtime installs may use `requirements.txt`.
5. Run commands from the repository root.
6. Run Stage Two smoke scripts as modules with `python -m scripts.stage_two.<module>`.
   Direct file-path execution such as `python scripts/stage_two/parser_smoke.py` is not supported because it can remove the repository root from `sys.path` and break `scripts.*` imports.

## Recommended Order

### 1. Bootstrap Storage

```powershell
python manage.py stage-two bootstrap-storage
```

Expected output:

```text
{
  "service": "stage-two bootstrap-storage",
  "root": "...",
  "created_count": <number>,
  "existing_count": <number>
}
```

This command is idempotent. It creates directories under `PATH_DATA_STORAGE` for Parquet, reports, DuckDB, logs, config, schemas, and temp data.

### 2. Apply Database Migrations

```powershell
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m alembic -c scripts/db/migrations/alembic.ini current
```

Expected state:

```text
5a38996dff5f (head)
```

### 3. Seed Parser Registry And Schema Version

```powershell
python manage.py stage-two seed-parser-registry
```

Expected output includes:

```text
"service": "stage-two seed-parser-registry"
"schema_name": "normalized_event"
"schema_version": "v1"
"inserted": <number>
"updated": <number>
```

The command is idempotent and loads `scripts/stage_two/parser_registry/parser_registry_seed.json`.

### 4. Ingest Catalog

```powershell
python manage.py stage-two catalog-ingest
```

What happens:

- `DatasetFileScanner` scans `PATH_FOLDER_DATASETS_FILTER` only.
- `branch`, `role`, `source_format`, dataset name, file size, and SHA-256 hash are inferred.
- `datasets`, `ingestion_runs`, and `dataset_files` are inserted or updated.
- Raw files are not modified.
- Only `TRAIN`, `VALIDATION`, and `TEST` are cataloged for Stage Two. `EXPERIMENTS` is ignored.

Typical statuses after ingestion:

| Status | Meaning |
| --- | --- |
| `REGISTERED` | New file was cataloged. |
| `CHANGED` | Existing file hash/metadata changed. |
| `DISCOVERED` | File was seen and can be promoted. |
| `EMPTY_FILE` | File exists but has no usable bytes. |
| `UNSUPPORTED_FORMAT` | Scanner found a format without active parser coverage. |

`PATH_FOLDER_DATASETS` is intentionally not ingested by this command. It remains the immutable raw source location and may contain extra datasets that are not part of the current processing corpus.

### 5. Check Parser Coverage

```powershell
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage host
python manage.py stage-two parser-coverage dns
```

Expected output columns:

```text
branch | role | source_format | files_count | parser_active | parser_class | parser_name | action
```

Important `action` values:

| Action | Meaning |
| --- | --- |
| `ready_for_normalization` | Catalog files exist and an active parser is available. |
| `parser_available_empty_bucket` | No files currently exist, but registry coverage exists. |
| `add_parser_registry_entry` | Catalog has a format not represented in registry. |
| `implement_parser_class` | Registry points to a class that cannot be imported. |
| `activate_parser_registry_entry` | Registry row exists but is inactive. |

Do not run broad normalization if `catalog_gap_rows` or `missing_parser_rows` is nonzero.

### 6. Mark Files Ready

Dry-run first:

```powershell
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
```

Apply only after reviewing counts:

```powershell
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
```

Fallback syntax:

```powershell
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
```

Only these statuses are promoted to `READY_FOR_PARSING`:

```text
REGISTERED, CHANGED, DISCOVERED
```

To retry files that failed after a parser or writer fix, use the explicit recovery mode:

```powershell
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --retry-failed --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --retry-failed --apply
```

Recovery mode only moves these statuses back to `READY_FOR_PARSING`:

```text
FAILED, SKIPPED, PARTIALLY_PARSED
```

It does not touch `PARSED` files. `mark-ready` writes EN/RU reports under `reports/{en,ru}/stage-two/status/`.

These statuses are not changed by the default mark-ready mode:

```text
EMPTY_FILE, FAILED, PARSED, PARTIALLY_PARSED, SKIPPED
```

### 7. Normalize One Format

```powershell
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 100
```

Fallback syntax:

```powershell
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
```

Expected output includes selected/processed/normalized counts, parser name/class, per-file status, and artifact id when an artifact is created.

`PARTIAL_SUCCESS` means the batch completed but at least one selected file failed, was skipped, or had no active parser. Successfully parsed files keep their `PARSED` status and `normalized_artifacts`; failed files can be retried with `mark-ready --retry-failed` after the underlying parser/writer issue is fixed.

### 8. Normalize A Branch

```powershell
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two normalize-all --branch dns --limit 1000
```

Fallback syntax:

```powershell
python manage.py stage-two normalize-all host:1000
```

`normalize-all` queries only `READY_FOR_PARSING` files and groups work by `role` and `source_format`.

`normalize-format`, `normalize-all`, and large `mark-ready` runs display a Rich progress bar when Rich is available. Non-interactive runs still print the final JSON-like summary and preserve normal exception output.

### 9. Run Checks

```powershell
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Expected result:

```text
status: SUCCESS
```

Reports are written under `PATH_DATA_STORAGE/reports/en/stage-two/` and `PATH_DATA_STORAGE/reports/ru/stage-two/`.

## Verifying Success

Use these checks for a normal parser workflow:

```powershell
python -m compileall manage.py config.py scripts tests
git diff --check
python -m scripts.db.smoke_check
python manage.py stage-two parser-coverage
python -m scripts.stage_two.parser_smoke
python -m scripts.stage_two.parser_input_smoke
python -m scripts.stage_two.parser_catalog_smoke
python -m scripts.stage_two.cli_operational_smoke
```

Catalog smoke and CLI smoke use synthetic files and roll back database changes.
Do not run these smoke scripts with `python scripts/stage_two/*.py`; use the module form above.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `DATABASE_URL` connection error | PostgreSQL is not running or URL is wrong. | Start PostgreSQL and verify `.env`. |
| `PATH_DATA_STORAGE must be configured` | Storage root is empty. | Set `PATH_DATA_STORAGE` and rerun `bootstrap-storage`. |
| `parser_active=no` in coverage | Missing or invalid registry/class mapping. | Update seed, implement class, run `seed-parser-registry`. |
| `selected=0` in `mark-ready` | No matching catalog rows or statuses are not eligible. | Check `parser-coverage` and `dataset_files.status`. |
| `selected=0` in `normalize-format` | Matching files are not `READY_FOR_PARSING`. | Run `mark-ready --apply` for that exact branch/role/format. |
| `PARTIAL_SUCCESS` | Some rows failed while others parsed. | Check parser run reports under `reports/*/stage-two/parser/`. |
| DuckDB report fails on missing Parquet | No normalized artifacts exist for the expected scope. | Normalize a small batch first. |

## Production Safety Notes

- Do not edit raw datasets to make parsing easier.
- Mixed `raw_fields_json`, `metadata_json`, `features_json`, and other `*_json` payloads are serialized before Parquet writes so PyArrow does not infer unstable nested types.
- Do not use `EXPERIMENTS` in Stage Two commands; supported processing roles are `TRAIN`, `VALIDATION`, and `TEST`.
- Do not store raw packet payloads, BSON streams, or full raw logs in PostgreSQL metadata.
- Do not mark whole branches ready without reviewing `parser-coverage`.
- Do not interpret full-corpus readiness from synthetic smoke tests alone.
