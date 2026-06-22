# Storage Architecture

## Storage Root

`PATH_DATA_STORAGE` is configured in `.env` and read by `config.py`. Generated artifacts, reports, temporary files, DuckDB database files, backups, and runtime Stage Two config should stay under this root.

Bootstrap command:

```bash
python manage.py stage-two bootstrap-storage
```

## Required Structure

`StorageBootstrapper.required_relative_paths()` creates:

```text
PATH_DATA_STORAGE/
  postgres/
  pgadmin/
  parquet/
    normalized/
    features/
    model_ready/
  duckdb/
    sql/
    exports/
  logs/stage-two/
  backups/
    postgres_catalog/
    metadata_exports/
  temp_data/
    ingestion/
    parser_runs/
    normalization/
    duckdb/
  schemas/
    normalized/
    features/
    model_ready/
  reports/
    ru/stage-two/
    en/stage-two/
  config/
```

The current bootstrap also creates report group directories such as `reports/ru/<group>` and `reports/en/<group>` for compatibility with existing constants.

## Stage One Storage Paths

| Config | Purpose |
|---|---|
| `PATH_FOLDER_DATASETS` | raw dataset root |
| `PATH_DNS_DATASETS` | `PATH_FOLDER_DATASETS/dns` |
| `PATH_HOST_DATASETS` | `PATH_FOLDER_DATASETS/host` |
| `PATH_FOLDER_DATASETS_FILTER` | sorted/filtered dataset root for Stage Two ingestion |
| `PATH_DNS_DATASETS_FILTER` | `PATH_FOLDER_DATASETS_FILTER/dns` |
| `PATH_HOST_DATASETS_FILTER` | `PATH_FOLDER_DATASETS_FILTER/host` |
| `PATH_TEMP_DATA` | JSON inventories and Stage One summaries |
| `PATH_REPORT` | reports root for Stage One and Stage Two |

Raw files under `PATH_FOLDER_DATASETS` are not modified. `sort` creates hardlinks/copies under `PATH_FOLDER_DATASETS_FILTER`.

## Parquet Paths

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

`ParquetArtifactWriter` returns both absolute and relative paths. Relative paths are stored in PostgreSQL artifact tables.

## DuckDB Paths

| Path | Purpose |
|---|---|
| `duckdb/proposal_analytics.duckdb` | default DuckDB database |
| `duckdb/sql/create_views.sql` | SQL template for views |
| `duckdb/exports/` | exports |

`DuckDBAnalyticsService` creates views directly from Parquet glob patterns. It does not copy Parquet data into PostgreSQL.

## Config and Schemas

Source schemas live in repository `schemas/`. Bootstrap also creates `PATH_DATA_STORAGE/schemas/...` directories for runtime copies/exports when needed.

Current schema loader reads:

- `schemas/normalized/normalized_event_v1.json`;
- `schemas/features/feature_artifact_v1.json`;
- `schemas/model_ready/model_ready_v1.json`.

## Operational Constraints

- `PATH_DATA_STORAGE` must be non-empty for bootstrap, Parquet writer, and DuckDB service.
- Generated artifacts should use relative paths in catalog for portability.
- Raw datasets should remain outside generated Parquet/report directories.
- Backups should include PostgreSQL catalog metadata and schema/config snapshots, not raw data copies unless explicitly planned.
