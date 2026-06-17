# PostgreSQL Catalog и SQLAlchemy слой

## Назначение

`scripts/db` содержит PostgreSQL Catalog для Stage Two. Catalog хранит metadata, статусы, версии схем, parser registry, parser runs и ссылки на artifacts. Большие normalized payloads не пишутся в PostgreSQL; они лежат в Parquet storage.

## Компоненты

| Путь | Назначение |
| --- | --- |
| `scripts/db/config.py` | Загружает `DATABASE_URL` и SQLAlchemy settings из окружения. |
| `scripts/db/session.py` | Создает engine, session factory и `session_scope()`. |
| `scripts/db/smoke_check.py` | Проверяет подключение и базовые запросы к DB. |
| `scripts/db/models/*` | SQLAlchemy ORM models. |
| `scripts/db/repositories/*` | Repository API для Stage Two services. |
| `scripts/db/migrations` | Alembic configuration и migrations для catalog schema. |

## Таблицы catalog

| Таблица | Модель | Назначение |
| --- | --- | --- |
| `datasets` | `Dataset` | Dataset-level metadata: name, slug, branch, role, source group, version, license, metadata. |
| `ingestion_runs` | `IngestionRun` | Запуск catalog ingestion: root path, status, counters, started/finished timestamps. |
| `dataset_files` | `DatasetFile` | Один raw file: path, relative path, extension, source_format, branch, role, hash, size, status, parser hints. |
| `parser_registry` | `ParserRegistry` | Parser strategies: branch, role, source_format, module/class, parser name/version, priority, active flag. |
| `schema_versions` | `SchemaVersion` | Версионированные schema contracts для normalized/features/model_ready layers. |
| `parser_runs` | `ParserRun` | Запуск parser на конкретном file: parser, schema, status, counters, started/finished, report path, errors. |
| `normalized_artifacts` | `NormalizedArtifact` | Ссылка на normalized Parquet artifact: path, hash, row count, schema, parser run. |
| `feature_artifacts` | `FeatureArtifact` | Ссылка на feature Parquet artifact и feature metadata. |
| `preprocessing_artifacts` | `PreprocessingArtifact` | Fitted preprocessing artifact metadata. |
| `model_ready_artifacts` | `ModelReadyArtifact` | Ссылка на model-ready artifact и split/data type metadata. |
| `label_mapping_rules` | `LabelMappingRule` | Безопасные правила label mapping. |
| `data_quality_reports` | `DataQualityReport` | DuckDB/leakage/readiness report metadata и details. |

## Статусы и constraints

Основные домены описаны в `scripts/db/models/constants.py`.

| Домен | Использование |
| --- | --- |
| `BRANCH_VALUES` | `dns`, `host`, `network`, `hybrid`. |
| `ROLE_VALUES` | `TRAIN`, `VALIDATION`, `TEST`. |
| `FILE_STATUS_VALUES` | `DISCOVERED`, `REGISTERED`, `CHANGED`, `READY_FOR_PARSING`, `PARSED`, `PARTIALLY_PARSED`, `FAILED`, `SKIPPED`, `EMPTY_FILE`, etc. |
| `RUN_STATUS_VALUES` | Статусы parser/check/artifact runs. |
| `SCHEMA_LAYER_VALUES` | `normalized`, `features`, `model_ready`. |

`mark-ready` изменяет только разрешенные исходные статусы:

```text
REGISTERED, CHANGED, DISCOVERED -> READY_FOR_PARSING
```

Он не меняет `EMPTY_FILE`, `FAILED`, `PARSED`, `PARTIALLY_PARSED`, `SKIPPED` без отдельного force-механизма.

## Repository layer

| Repository | Назначение |
| --- | --- |
| `BaseRepository` | Общие CRUD helpers. |
| `DatasetRepository` | Dataset upsert/lookup. |
| `DatasetFileRepository` | Raw file upsert/lookup, selection by branch/role/source_format/status. |
| `IngestionRepository` | Ingestion run lifecycle и counters. |
| `ParserRepository` | Parser registry lookup, parser run registration, artifact registration helpers. |
| `SchemaRepository` | Schema version upsert/lookup. |
| `ArtifactRepository` | Normalized/feature/model-ready artifact registration. |
| `PreprocessingRepository` | Preprocessing artifact registration. |
| `LabelRepository` | Label mapping rules. |
| `DataQualityRepository` | Data quality report registration. |

## Session lifecycle

DB операции выполняются внутри `session_scope()`:

```python
from scripts.db.session import session_scope

with session_scope() as session:
    ...
```

`session_scope()` отвечает за commit/rollback/close. Services не должны открывать вложенные независимые transactions без необходимости. Для batch normalization безопасный паттерн - controlled per-file/per-batch commit через service layer, а не manual commit внутри repository.

## Связь команд и таблиц

| Команда | Таблицы |
| --- | --- |
| `catalog-ingest` | `ingestion_runs`, `datasets`, `dataset_files`. |
| `seed-parser-registry` | `schema_versions`, `parser_registry`. |
| `parser-coverage` | Читает `dataset_files`, `parser_registry`, `schema_versions`; пишет report files. |
| `mark-ready` | Обновляет `dataset_files.status`. |
| `normalize-format` / `normalize-all` | Читает `dataset_files`/registry/schema; пишет `parser_runs`, `normalized_artifacts`, обновляет file status. |
| `run-duckdb-checks` | Читает artifact metadata и Parquet; пишет `data_quality_reports`. |
| `run-leakage-checks` | Читает catalog/artifact metadata; пишет `data_quality_reports`. |

## Alembic и smoke

Типовая проверка DB слоя:

```powershell
python -m alembic -c scripts/db/migrations/alembic.ini current
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m scripts.db.smoke_check
```

Если `DATABASE_URL` недоступен, DB-dependent CLI завершится ошибкой подключения. Это не проблема parser code, но блокер для catalog/normalization smoke.
