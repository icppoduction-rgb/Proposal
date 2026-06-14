# PostgreSQL Catalog и SQLAlchemy слой

## Назначение

`scripts/db` содержит инфраструктуру PostgreSQL Catalog для Stage Two. Catalog хранит metadata о datasets, raw files, parser registry, schema versions, parser runs, normalized/features/model-ready artifacts, label rules и quality reports. Большие данные не пишутся в PostgreSQL; payload хранится в raw files и Parquet storage.

## Компоненты

| Путь | Назначение |
|---|---|
| `scripts/db/config.py` | Загружает `DATABASE_URL` и параметры SQLAlchemy из окружения. |
| `scripts/db/session.py` | Создает engine/session factory и `session_scope()`. |
| `scripts/db/smoke_check.py` | Проверка подключения/работоспособности DB. |
| `scripts/db/models/*` | SQLAlchemy ORM модели. |
| `scripts/db/repositories/*` | Repository API для Stage Two services. |
| `scripts/db/migrations` | Alembic environment и migration `5a38996dff5f_create_stage_two_catalog_schema.py`. |

## ORM таблицы

| Таблица | Модель | Назначение |
|---|---|---|
| `datasets` | `Dataset` | Dataset-level metadata: name, slug, branch, role, source group, version, license, metadata_json. |
| `ingestion_runs` | `IngestionRun` | Запуски catalog ingestion: root path, status, counters, started/finished timestamps. |
| `dataset_files` | `DatasetFile` | Один raw file: path, extension, source_format, hash, role, branch, status, parser hints, metadata. |
| `parser_registry` | `ParserRegistry` | Доступные parser strategies: parser name/version/class/module, branch, source_format, role, priority, active flag. |
| `schema_versions` | `SchemaVersion` | Версионированные схемы normalized/features/model-ready layers. Stage Two seed обязан создавать запись normalized schema. |
| `parser_runs` | `ParserRun` | Запуск parser на конкретном raw file: parser, schema, status, counters, errors. |
| `normalized_artifacts` | `NormalizedArtifact` | Ссылки на normalized Parquet artifacts и schema version. |
| `feature_artifacts` | `FeatureArtifact` | Ссылки на feature Parquet artifacts, feature schema, counters, excluded columns. |
| `preprocessing_artifacts` | `PreprocessingArtifact` | Fitted preprocessing artifacts и связь с feature/model-ready layers. |
| `model_ready_artifacts` | `ModelReadyArtifact` | Финальные model-ready artifacts, data type, schema, counters, label distribution. |
| `label_mapping_rules` | `LabelMappingRule` | Правила mapping labels для branch/source/dataset/format. |
| `data_quality_reports` | `DataQualityReport` | Отчеты DuckDB/leakage/readiness checks и их details_json. |

## Constraints и статусы

Модели используют check constraints для ролей, веток, статусов и layer/data_type значений. Основные домены задаются в `scripts/db/models/constants.py`.

| Домен | Использование |
|---|---|
| `BRANCH_VALUES` | `dns`, `host`, `network`, `hybrid` в catalog/artifacts/parser registry. |
| `ROLE_VALUES` | `TRAIN`, `VALIDATION`, `TEST`. |
| `FILE_STATUS_VALUES` | Статусы raw files, включая `REGISTERED`, `READY_FOR_PARSING`, unsupported/changed/error состояния. |
| `RUN_STATUS_VALUES` | Статусы parser/artifact/check runs. |
| `SCHEMA_LAYER_VALUES` | `normalized`, `features`, `model_ready`. |

## Репозитории

| Репозиторий | Назначение |
|---|---|
| `BaseRepository` | Общие CRUD helpers. |
| `DatasetRepository` | Upsert/lookup datasets. |
| `DatasetFileRepository` | Upsert/lookup raw files, выборка `get_files_ready_for_parsing(branch, limit)`. |
| `IngestionRepository` | Регистрация ingestion runs и counters. |
| `ParserRepository` | Parser registry lookup и parser run/artifact registration. |
| `SchemaRepository` | Upsert/lookup schema_versions. |
| `ArtifactRepository` | Регистрация normalized/feature/model-ready artifacts. |
| `PreprocessingRepository` | Регистрация preprocessing artifacts. |
| `LabelRepository` | Label mapping rules. |
| `DataQualityRepository` | Регистрация quality reports. |

## Session lifecycle

Stage Two services используют `session_scope()`:

```text
with session_scope() as session:
    repository = DatasetFileRepository(session)
    ...
```

Контекстный менеджер отвечает за commit/rollback/close. CLI-команды Stage Two открывают session на время операции и передают ее service/repository слоям.

## Связь с Stage Two

| Stage Two шаг | Таблицы |
|---|---|
| `catalog-ingest` | `ingestion_runs`, `datasets`, `dataset_files` |
| `seed-parser-registry` | `schema_versions`, `parser_registry` |
| `normalize-dns` / `normalize-host` | `dataset_files`, `parser_registry`, `schema_versions`, `parser_runs`, `normalized_artifacts` |
| `run-duckdb-checks` / `run-leakage-checks` | `data_quality_reports` |
| feature/model-ready APIs | `feature_artifacts`, `preprocessing_artifacts`, `model_ready_artifacts` |
| `trace-artifact` | read path across artifact tables back to `dataset_files` |

## Важные правила для разработки

- Новая normalized schema должна быть зарегистрирована в `schema_versions`; parser registry должен ссылаться на имя/версию схемы.
- Planned/unsupported parsers не должны иметь `is_active=true`.
- PostgreSQL хранит metadata и traceability, а не строки событий.
- Для сохранения traceability нельзя создавать Parquet без записи catalog artifact.
