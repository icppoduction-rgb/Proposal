# Stage Two Storage Architecture

Stage Two stores large data outside PostgreSQL. The root is configured through `PATH_DATA_STORAGE`, and `bootstrap-storage` creates the required directory structure through `scripts/stage_two/storage/bootstrap.py`.

## Purpose of `PATH_DATA_STORAGE`

`PATH_DATA_STORAGE` is the dedicated storage root for Stage Two artifacts:

- Parquet normalized/features/model-ready tables;
- DuckDB SQL files, exports, and local `.duckdb` databases;
- runtime logs;
- temp data for ingestion/parser/normalization/DuckDB;
- catalog metadata backups;
- runtime schema copies;
- reports in English and Russian.

Raw dataset files are not copied into `PATH_DATA_STORAGE` during catalog ingestion. Their path and hash are stored in PostgreSQL (`dataset_files.file_path`, `dataset_files.file_hash_sha256`).

## Base Structure

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
  logs/
    stage-two/
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
    ru/
      stage-two/
        parser/
        normalization/
        quality/
        leakage/
        schema_mismatch/
    en/
      stage-two/
        parser/
        normalization/
        quality/
        leakage/
        schema_mismatch/
  config/
```

`StorageBootstrapper.required_relative_paths()` also creates role-aware directories for normalized/features/model-ready layers, so `TRAIN`, `VALIDATION`, and `TEST` are not mixed.

## Parquet Layers

| Layer | Path | Writer |
| --- | --- | --- |
| normalized | `parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` | `ParquetArtifactWriter.write_normalized()` through DNS/Host normalization services |
| features | `parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` | `FeatureArtifactWriter.write_and_register()` |
| model-ready | `parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}` | `ModelReadyRegistryService.write_table_artifact()` |

Stage Two writes the normalized layer. Feature/model-ready layers are now built by the Stage Three `extract-features` and `build-model-ready` commands from `scripts/stage_three/cli.py`; Stage Two storage bootstrap creates these directories up front to keep one shared `PATH_DATA_STORAGE`.

## Reports

| Report group | Example files | Writer |
| --- | --- | --- |
| parser | coverage/status reports | parser coverage/status tools |
| normalization | parser run summaries | normalization services/runners |
| quality | `duckdb_analytics_report.json`, data quality reports | `DuckDBAnalyticsService`, `DataQualityChecker` |
| leakage | leakage reports EN/RU | `LeakageChecker` |
| stage-two root | readiness/e2e reports | `readiness_check`, `e2e_dry_run` |

`DuckDBAnalyticsService` saves a JSON report to `reports/en/stage-two/quality/duckdb_analytics_report.json`. `DataQualityChecker` and `LeakageChecker` save reports under EN/RU report roots.

## Temp Data

`temp_data` is used for temporary ingestion, parser run, normalization, and DuckDB outputs. `e2e_dry_run` creates a synthetic workspace under:

```text
temp_data/stage_two_e2e_dry_run/
```

Data under `temp_data` is not a source of truth. The source of truth for metadata is PostgreSQL Catalog, and the source of truth for large tables is Parquet artifacts.

## Config and Schemas

| Path | Purpose |
| --- | --- |
| `config/label_mapping_rules.json` | External label mapping rules, if created in storage. |
| `schemas/normalized/` | Runtime schema copies for the normalized layer. |
| `schemas/features/` | Runtime schema copies for the feature layer. |
| `schemas/model_ready/` | Runtime schema copies for the model-ready layer. |

Project schema contracts are stored in the repository:

```text
schemas/normalized/normalized_event_v1.json
schemas/features/feature_artifact_v1.json
schemas/model_ready/model_ready_v1.json
```

## Limitations

- Storage bootstrap creates directories, but it does not start PostgreSQL and does not apply Alembic migrations.
- PostgreSQL stores artifact paths, but it does not store large normalized/features/model-ready tables.
- Moving or deleting files under `PATH_DATA_STORAGE/parquet` breaks `normalized_artifacts`, `feature_artifacts`, `model_ready_artifacts`, and traceability.
- `PATH_FOLDER_DATASETS_FILTER` and `PATH_DATA_STORAGE` must remain separate responsibility zones: the first contains the input tree, the second contains Stage Two outputs.
