# Parquet and DuckDB Artifacts

## Why Parquet

Parquet is used for large generated tables:

- normalized events;
- feature artifacts;
- model-ready artifacts.

PostgreSQL Catalog stores metadata and paths, not row tables. This keeps the catalog compact and allows DuckDB to run SQL checks over columnar data.

## Writer

File: `scripts/stage_two/parquet/writer.py`.

Class: `ParquetArtifactWriter`.

Default compression:

```text
zstd
```

`_write_rows()`:

1. normalizes JSON suffix columns (`*_json`) into deterministic JSON strings;
2. builds a PyArrow table;
3. writes Parquet;
4. returns `ParquetWriteResult`.

`ParquetWriteResult`:

| Field | Meaning |
|---|---|
| `absolute_path` | full filesystem path |
| `relative_path` | path relative to `PATH_DATA_STORAGE` |
| `row_count` | number of written rows |
| `file_size_bytes` | Parquet file size |
| `content_hash_sha256` | optional output hash, empty if hashing is disabled |

## Artifact Paths

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

## Catalog Registration

| Writer method | Catalog table |
|---|---|
| `register_normalized_artifact()` | `normalized_artifacts` |
| `register_feature_artifact()` | `feature_artifacts` |
| `register_model_ready_artifact()` | `model_ready_artifacts` |

Catalog stores relative paths:

- `normalized_artifacts.normalized_path`;
- `feature_artifacts.feature_path`;
- `model_ready_artifacts.artifact_path`.

## DuckDB Service

File: `scripts/stage_two/duckdb/service.py`.

Class: `DuckDBAnalyticsService`.

Default database:

```text
PATH_DATA_STORAGE/duckdb/proposal_analytics.duckdb
```

Views:

| View | Pattern |
|---|---|
| `normalized_all` | `parquet/normalized/**/*.parquet` |
| `features_all` | `parquet/features/**/*.parquet` |
| `model_ready_all` | `parquet/model_ready/**/*.parquet` |

Views are created with:

```sql
read_parquet('<glob>', union_by_name = true, filename = true)
```

If no files are found, the service creates empty views with stable placeholder columns.

## DuckDB Checks

`run_checks()` executes:

- row count checks grouped by available role/branch columns or filename path;
- missing required column checks;
- split contamination check;
- schema mismatch check.

Required columns:

| View | Required columns |
|---|---|
| `normalized_all` | `event_uid`, `dataset_role`, `branch`, `source_file_path` |
| `features_all` | `role`, `branch`, `feature_group` |
| `model_ready_all` | `filename` |

Report path:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

`register_report()` writes an aggregate row to `data_quality_reports`.

## SQL Template

`scripts/stage_two/duckdb/sql/create_views.sql` contains a direct SQL template with placeholder `${PATH_DATA_STORAGE}`. The Python service is safer at runtime because it handles empty views and path escaping.
