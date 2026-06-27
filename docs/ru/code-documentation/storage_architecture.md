# Архитектура storage

## Корень storage

`PATH_DATA_STORAGE` задается в `.env` и читается в `config.py`. Все generated artifacts, reports, temporary files, база DuckDB, backups и runtime config Stage Two должны находиться внутри этого корня.

Команда bootstrap:

```bash
python manage.py stage-two bootstrap-storage
```

## Обязательная структура

`StorageBootstrapper.required_relative_paths()` создает:

```text
PATH_DATA_STORAGE/
  postgres/
  pgadmin/
  parquet/
    normalized/
      dns/TRAIN/
      dns/VALIDATION/
      dns/TEST/
      host/TRAIN/
      host/VALIDATION/
      host/TEST/
      network/TRAIN/
      network/VALIDATION/
      network/TEST/
      hybrid/TRAIN/
      hybrid/VALIDATION/
      hybrid/TEST/
    features/
      dns_features/
      host_syscall_features/
      host_eventlog_features/
      host_metrics_features/
      network_flow_features/
      hybrid_features/
      sequence_features/
    model_ready/
      tabular/
      labels/
      sequences/
      preprocessing/
      split_index/
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
      parser/
      normalization/
      quality/
      leakage/
      schema_mismatch/
    en/stage-two/
      parser/
      normalization/
      quality/
      leakage/
      schema_mismatch/
  config/
```

Фактический bootstrap также создает report group directories в `reports/ru/<group>` и `reports/en/<group>` для совместимости с текущими constants.

## Пути storage для Stage One

Stage One использует:

| Config | Назначение |
|---|---|
| `PATH_FOLDER_DATASETS` | корень raw datasets |
| `PATH_DNS_DATASETS` | `PATH_FOLDER_DATASETS/dns` |
| `PATH_HOST_DATASETS` | `PATH_FOLDER_DATASETS/host` |
| `PATH_FOLDER_DATASETS_FILTER` | корень sorted/filtered datasets для Stage Two ingestion |
| `PATH_DNS_DATASETS_FILTER` | `PATH_FOLDER_DATASETS_FILTER/dns` |
| `PATH_HOST_DATASETS_FILTER` | `PATH_FOLDER_DATASETS_FILTER/host` |
| `PATH_TEMP_DATA` | JSON inventories и Stage One summaries |
| `PATH_REPORT` | корень reports Stage One и Stage Two |

Raw files в `PATH_FOLDER_DATASETS` не изменяются. `sort` создает hardlinks/copies в `PATH_FOLDER_DATASETS_FILTER`.

## Пути Parquet

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

`ParquetArtifactWriter` возвращает абсолютный и относительный path. Относительный path сохраняется в PostgreSQL artifact tables.

## Пути DuckDB

| Путь | Назначение |
|---|---|
| `duckdb/proposal_analytics.duckdb` | DuckDB database по умолчанию |
| `duckdb/sql/create_views.sql` | SQL template для views |
| `duckdb/exports/` | exports |

`DuckDBAnalyticsService` может создавать views напрямую из Parquet glob patterns. Он не копирует Parquet data в PostgreSQL.

## Отчеты

| Тип отчета | Путь |
|---|---|
| DuckDB analytics | `reports/en/stage-two/quality/duckdb_analytics_report.json` |
| Quality report | `reports/{en,ru}/stage-two/quality/quality_report.json` |
| Leakage report | `reports/{en,ru}/stage-two/leakage/leakage_report.json` |
| Parser reports | генерируются `scripts/stage_two/reports` внутри storage reports |

## Config и schemas

Исходные schemas проекта находятся в repository `schemas/`. Bootstrap также создает directories `PATH_DATA_STORAGE/schemas/...` для runtime copies/exports, если они нужны.

Текущий загрузчик схем читает:

- `schemas/normalized/normalized_event_v1.json`;
- `schemas/features/feature_artifact_v1.json`;
- `schemas/model_ready/model_ready_v1.json`.

## Эксплуатационные ограничения

- `PATH_DATA_STORAGE` должен быть непустым для bootstrap, Parquet writer и DuckDB service.
- Generated artifacts должны использовать relative paths в catalog для portability.
- Raw datasets должны оставаться вне generated Parquet/report directories.
- Backups должны включать PostgreSQL catalog metadata и schema/config snapshots, а не копии raw data, если это явно не запланировано.
