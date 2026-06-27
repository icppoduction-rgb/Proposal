# Архитектура storage Stage Two

Stage Two хранит большие данные вне PostgreSQL. Корень задается переменной `PATH_DATA_STORAGE`, а `bootstrap-storage` создает обязательную структуру директорий через `scripts/stage_two/storage/bootstrap.py`.

## Назначение `PATH_DATA_STORAGE`

`PATH_DATA_STORAGE` - отдельный storage root для Stage Two artifacts:

- Parquet normalized/features/model-ready tables;
- DuckDB SQL files, exports и локальные `.duckdb` databases;
- runtime logs;
- temp data для ingestion/parser/normalization/DuckDB;
- backups catalog metadata;
- runtime schema copies;
- reports на русском и английском.

Raw dataset files не копируются в `PATH_DATA_STORAGE` при catalog ingestion. Их путь и хеш сохраняются в PostgreSQL (`dataset_files.file_path`, `dataset_files.file_hash_sha256`).

## Базовая структура

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

`StorageBootstrapper.required_relative_paths()` также создает role-aware поддиректории для normalized/features/model-ready layers, чтобы `TRAIN`, `VALIDATION` и `TEST` не смешивались.

## Parquet layers

| Layer | Путь | Кто пишет |
| --- | --- | --- |
| normalized | `parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` | `ParquetArtifactWriter.write_normalized()` через DNS/Host normalization services |
| features | `parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` | `FeatureArtifactWriter.write_and_register()` |
| model-ready | `parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}` | `ModelReadyRegistryService.write_table_artifact()` |

В текущем CLI есть команды normalization и checks. Полноценная CLI-команда feature/model-ready build не реализована; соответствующий слой представлен contracts/writers/registry services.

## Reports

| Report group | Примеры файлов | Кто пишет |
| --- | --- | --- |
| parser | coverage/status reports | parser coverage/status tools |
| normalization | parser run summaries | normalization services/runners |
| quality | `duckdb_analytics_report.json`, data quality reports | `DuckDBAnalyticsService`, `DataQualityChecker` |
| leakage | leakage reports RU/EN | `LeakageChecker` |
| stage-two root | readiness/e2e reports | `readiness_check`, `e2e_dry_run` |

`DuckDBAnalyticsService` сохраняет JSON report в `reports/en/stage-two/quality/duckdb_analytics_report.json`. `DataQualityChecker` и `LeakageChecker` сохраняют отчеты в RU/EN report roots.

## Temp data

`temp_data` используется для временных результатов ingestion, parser runs, normalization и DuckDB. `e2e_dry_run` создает synthetic workspace под:

```text
temp_data/stage_two_e2e_dry_run/
```

Данные из `temp_data` нельзя считать source of truth. Source of truth для metadata - PostgreSQL Catalog, для больших таблиц - Parquet artifacts.

## Config и schemas

| Путь | Назначение |
| --- | --- |
| `config/label_mapping_rules.json` | Внешние label mapping rules, если файл создан в storage. |
| `schemas/normalized/` | Runtime schema copies для normalized layer. |
| `schemas/features/` | Runtime schema copies для feature layer. |
| `schemas/model_ready/` | Runtime schema copies для model-ready layer. |

Проектные schema contracts находятся в репозитории:

```text
schemas/normalized/normalized_event_v1.json
schemas/features/feature_artifact_v1.json
schemas/model_ready/model_ready_v1.json
```

## Ограничения

- Storage bootstrap создает директории, но не запускает PostgreSQL и не применяет Alembic migrations.
- PostgreSQL хранит пути к artifacts, но не хранит большие normalized/features/model-ready таблицы.
- Удаление или перенос файлов в `PATH_DATA_STORAGE/parquet` ломает `normalized_artifacts`, `feature_artifacts`, `model_ready_artifacts` и traceability.
- `PATH_FOLDER_DATASETS_FILTER` и `PATH_DATA_STORAGE` должны быть разными зонами ответственности: первая содержит input tree, вторая - Stage Two outputs.
