# PostgreSQL catalog schema

Схема создается Alembic migration `scripts/db/migrations/versions/5a38996dff5f_create_stage_two_catalog_schema.py`. ORM-модели находятся в `scripts/db/models`, repository layer - в `scripts/db/repositories`.

## Основные таблицы

| Таблица | Назначение |
| --- | --- |
| `datasets` | Логические датасеты с `branch`, `role`, `slug`, source metadata. |
| `ingestion_runs` | Запуски сканирования root-путей и счетчики найденных файлов. |
| `dataset_files` | Raw files catalog: путь, формат, роль, ветка, hash, статус. |
| `parser_registry` | Активные parser metadata по branch/source_format/role. |
| `schema_versions` | Версии схем normalized, features и model_ready. |
| `parser_runs` | Запуски парсеров для конкретных `dataset_files`. |
| `normalized_artifacts` | Метаданные Parquet normalized outputs. |
| `feature_artifacts` | Метаданные Parquet feature outputs. |
| `preprocessing_artifacts` | TRAIN-fitted preprocessing objects и metadata. |
| `model_ready_artifacts` | X/y/sequence/split/preprocessing metadata artifacts. |
| `label_mapping_rules` | Правила канонизации labels. |
| `data_quality_reports` | Отчеты quality/leakage/DuckDB checks. |

## Статусы

`dataset_files.status` поддерживает:

```text
DISCOVERED, REGISTERED, CHANGED, EMPTY_FILE, UNSUPPORTED_FORMAT,
READY_FOR_PARSING, PARSED, PARTIALLY_PARSED, FAILED, SKIPPED
```

Artifact/report статусы поддерживают:

```text
PENDING, RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED, SKIPPED, BLOCKED
```

## Traceability links

Цепочка прослеживаемости:

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

CLI-проверка:

```powershell
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Ограничения

- `role` и `branch` валидируются check constraints.
- `preprocessing_artifacts.fitted_on_role` должен быть `TRAIN`.
- PostgreSQL хранит metadata и paths, а не большие табличные данные.
