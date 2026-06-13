# PostgreSQL Catalog Schema

The schema is created by Alembic migration `scripts/db/migrations/versions/5a38996dff5f_create_stage_two_catalog_schema.py`. ORM models are in `scripts/db/models`; repository classes are in `scripts/db/repositories`.

## Main Tables

| Table | Purpose |
| --- | --- |
| `datasets` | Logical datasets with `branch`, `role`, `slug`, and source metadata. |
| `ingestion_runs` | Root scan runs and discovered-file counters. |
| `dataset_files` | Raw file catalog: path, format, role, branch, hash, status. |
| `parser_registry` | Active parser metadata by branch/source_format/role. |
| `schema_versions` | Versions for normalized, features, and model_ready schemas. |
| `parser_runs` | Parser executions for individual `dataset_files`. |
| `normalized_artifacts` | Metadata for normalized Parquet outputs. |
| `feature_artifacts` | Metadata for feature Parquet outputs. |
| `preprocessing_artifacts` | TRAIN-fitted preprocessing objects and metadata. |
| `model_ready_artifacts` | X/y/sequence/split/preprocessing metadata artifacts. |
| `label_mapping_rules` | Canonical label mapping rules. |
| `data_quality_reports` | Quality, leakage, and DuckDB reports. |

## Status Values

`dataset_files.status` supports:

```text
DISCOVERED, REGISTERED, CHANGED, EMPTY_FILE, UNSUPPORTED_FORMAT,
READY_FOR_PARSING, PARSED, PARTIALLY_PARSED, FAILED, SKIPPED
```

Artifact/report statuses support:

```text
PENDING, RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED, SKIPPED, BLOCKED
```

## Traceability Links

The trace chain is:

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

CLI check:

```powershell
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Constraints

- `role` and `branch` are validated by check constraints.
- `preprocessing_artifacts.fitted_on_role` must be `TRAIN`.
- PostgreSQL stores metadata and paths, not large tabular artifacts.
