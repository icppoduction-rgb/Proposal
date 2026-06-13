# Stage Two Storage Architecture

The storage root comes from `PATH_DATA_STORAGE` in `.env`. Bootstrap logic lives in `scripts/stage_two/storage/bootstrap.py` and is exposed through:

```powershell
python manage.py stage-two bootstrap-storage
```

The operation is idempotent: existing directories are not deleted or overwritten.

## Main Zones

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

## Parquet Partitioning

Normalized events:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Feature artifacts:

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Model-ready tables:

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

`branch` is `dns`, `host`, `network`, or `hybrid`; `role` is `TRAIN`, `VALIDATION`, `TEST`, or `EXPERIMENTS`.

## PostgreSQL Scope

PostgreSQL catalog stores:

- raw and generated file paths;
- SHA-256 hashes, sizes, and row counters;
- ingestion, parsing, artifact, and quality statuses;
- raw -> normalized -> features -> model-ready relationships;
- label mapping rules and parser registry rows.

Large normalized events/features/model-ready rows are not stored in PostgreSQL. They remain in Parquet.
