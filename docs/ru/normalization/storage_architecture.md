# Архитектура хранилища Stage Two

Корневой путь берется из `PATH_DATA_STORAGE` в `.env`. Bootstrap реализован в `scripts/stage_two/storage/bootstrap.py` и вызывается командой:

```powershell
python manage.py stage-two bootstrap-storage
```

Операция идемпотентна: существующие директории не удаляются и не перезаписываются.

## Основные зоны

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

## Parquet partitioning

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

Где `branch` - `dns`, `host`, `network` или `hybrid`; `role` - `TRAIN`, `VALIDATION`, `TEST` или `EXPERIMENTS`.

## Что хранится в PostgreSQL

PostgreSQL catalog хранит:

- пути к raw и generated файлам;
- SHA-256 хеши, размеры и счетчики строк;
- статусы ingestion, parsing, artifact generation и quality checks;
- связи raw -> normalized -> features -> model-ready;
- label mapping rules и parser registry.

Большие строки normalized events/features/model-ready не пишутся в PostgreSQL. Они остаются в Parquet.
