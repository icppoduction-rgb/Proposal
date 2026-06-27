# PostgreSQL Catalog и SQLAlchemy слой

PostgreSQL Catalog хранит metadata, статусы, связи, пути, хеши и отчеты Stage Two. Большие normalized/features/model-ready таблицы не пишутся в PostgreSQL: они сохраняются как Parquet в `PATH_DATA_STORAGE`, а catalog хранит только ссылки и агрегированную metadata.

## Где находится код

| Компонент | Путь |
| --- | --- |
| DB settings | `scripts/db/config.py` |
| Engine/session | `scripts/db/session.py` |
| Models | `scripts/db/models/*` |
| Constants/status values | `scripts/db/models/constants.py` |
| Repositories | `scripts/db/repositories/*` |
| Alembic migrations | `scripts/db/migrations/*` |
| Smoke check | `scripts/db/smoke_check.py` |

`session_scope()` создает SQLAlchemy session, делает `commit()` при успешном выходе и `rollback()` при исключении.

## Миграции и smoke check

```bash
alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m scripts.db.smoke_check
```

Smoke check создает временные записи внутри транзакции и проверяет:

- unique/check constraints;
- создание `datasets`, `ingestion_runs`, `dataset_files`;
- parser run lifecycle;
- регистрацию normalized, feature, preprocessing, model-ready artifacts;
- запрет `TEST` для preprocessing fit;
- регистрацию quality report.

## Основные constraints

| Constraint group | Значения |
| --- | --- |
| branch | `dns`, `host`, `network`, `hybrid` |
| active dataset role | `TRAIN`, `VALIDATION`, `TEST` |
| DB role values | `TRAIN`, `VALIDATION`, `TEST`, `EXPERIMENTS` |
| file status | `DISCOVERED`, `REGISTERED`, `CHANGED`, `EMPTY_FILE`, `UNSUPPORTED_FORMAT`, `READY_FOR_PARSING`, `PARSED`, `PARTIALLY_PARSED`, `FAILED`, `SKIPPED` |
| run status | `PENDING`, `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED` |
| parser run status | `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED` |
| schema layer | `normalized`, `features`, `model_ready` |
| label status | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label` |
| quality severity | `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

Catalog scanner Stage Two активирует только `TRAIN`, `VALIDATION`, `TEST`. `EXPERIMENTS` существует как DB value, но не должен попадать в основной normalization pipeline.

## Таблицы

### `datasets`

Назначение: логическая группа файлов одного dataset/branch/role/source group.

Пишут: `CatalogIngestionService`, DB smoke check.  
Читают: normalization services, artifact registration, readiness checks.

Ключевые поля: `id`, `name`, `slug`, `branch`, `role`, `source_group`, `root_path`, timestamps/metadata.

Связи: `datasets.id -> dataset_files.dataset_id`, `normalized_artifacts.dataset_id`, `feature_artifacts.dataset_id`.

### `ingestion_runs`

Назначение: запуск сканирования input tree.

Пишут: `CatalogIngestionService`.  
Читают: diagnostics/readiness.

Ключевые поля: `id`, `root_path`, `root_path_kind`, `branch`, `role`, counters, `status`, timestamps, error fields.

### `dataset_files`

Назначение: metadata raw/input файла, включая путь, размер, hash, role, branch, source_format и lifecycle status.

Пишут: catalog ingestion, large-file splitter при `--register`, status tools.  
Читают: parser resolver, normalization runners/services, readiness raw hash check.

Ключевые поля: `dataset_id`, `ingestion_run_id`, `file_path`, `relative_path`, `file_name`, `file_extension`, `source_format`, `file_size_bytes`, `file_hash_sha256`, `role`, `branch`, `status`, `error_message`, `metadata_json`.

Статусы: `REGISTERED` после ingestion, `READY_FOR_PARSING` после `mark-ready`, `PARSED`/`PARTIALLY_PARSED`/`FAILED` после normalization, `UNSUPPORTED_FORMAT` при отсутствии parser.

### `parser_registry`

Назначение: declarative registry parser implementations.

Пишут: `ParserRegistrySeeder`.  
Читают: `ParserResolver`, normalization services, parser coverage, readiness.

Ключевые поля: `parser_name`, `parser_version`, `branch`, `source_format`, `supported_role`, `priority`, `normalized_schema_name`, `normalized_schema_version`, `parser_module`, `parser_class`, `is_active`, `config_json`.

Resolver выбирает active parser по `branch/source_format`, role-specific entry или `supported_role IS NULL`, сортирует по `priority` и `id`.

### `schema_versions`

Назначение: catalog registry schema contracts.

Пишут: parser registry seed, repositories/smoke.  
Читают: parser runs, readiness, normalization.

Ключевые поля: `schema_name`, `schema_version`, `layer`, `branch`, `schema_path`, `schema_hash_sha256`, `is_active`.

### `parser_runs`

Назначение: один запуск parser для одного `dataset_files.id`.

Пишут: DNS/Host normalization services.  
Читают: artifact registration, traceability, readiness.

Ключевые поля: `file_id`, `parser_registry_id`, `schema_version_id`, `parser_name`, `parser_version`, `status`, counters (`rows_read`, `rows_parsed`, `rows_failed`, `events_emitted`), `output_parquet_path`, error samples/timestamps.

Статусы: `RUNNING`, затем `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED` или `SKIPPED`.

### `normalized_artifacts`

Назначение: metadata normalized Parquet artifact.

Пишут: `ParquetArtifactWriter.register_normalized_artifact()`.  
Читают: feature writer/registry services, DuckDB/readiness, traceability.

Ключевые поля: `dataset_id`, `file_id`, `parser_run_id`, `schema_version_id`, `role`, `branch`, `modality`, `source_format`, `normalized_path`, `schema_name`, `schema_version`, `row_count`, `event_count`, `file_size_bytes`, `content_hash_sha256`, `status`.

### `feature_artifacts`

Назначение: metadata feature Parquet artifact.

Пишут: `FeatureArtifactWriter.write_and_register()`.  
Читают: model-ready registry, leakage checks, readiness, traceability.

Ключевые поля: `dataset_id`, `normalized_artifact_id`, `role`, `branch`, `feature_group`, `feature_path`, `feature_schema_name`, `feature_schema_version`, `row_count`, `sample_count`, `feature_count`, `excluded_columns_json`, `label_distribution_json`, `status`.

В production traceability `normalized_artifact_id` должен быть заполнен. Readiness check считает artifact без этой связи ошибкой.

### `preprocessing_artifacts`

Назначение: metadata scaler/encoder/other preprocessing objects.

Пишут: `ModelReadyRegistryService.register_preprocessing_artifact()`.  
Читают: model-ready registry, leakage checks/readiness.

Ключевые поля: `branch`, `feature_group`, `preprocessing_type`, `artifact_path`, `fitted_on_role`, `fitted_on_feature_artifact_id`, `schema_version`, `object_version`, `columns_json`, `params_json`, `status`.

Ограничение: `fitted_on_role` должен быть `TRAIN`. Код отклоняет `TEST`.

### `model_ready_artifacts`

Назначение: metadata model-ready X/y/sequence/split/preprocessing tables or files.

Пишут: `ModelReadyRegistryService.write_table_artifact()` и `register_external_artifact()`.  
Читают: leakage checks, traceability, readiness.

Ключевые поля: `feature_artifact_id`, `preprocessing_artifact_id`, `role`, `branch`, `data_type`, `artifact_path`, `schema_name`, `schema_version`, `sample_count`, `feature_count`, `excluded_columns_json`, `label_distribution_json`, `sequence_length`, `status`.

`data_type` поддерживает `X`, `y`, `sequence`, `split_index`, `preprocessing_metadata`. Для `X` registry validates forbidden leakage columns.

### `label_mapping_rules`

Назначение: explicit/external rules для label resolver.

Пишут: `LabelRepository` или конфигурационные загрузчики, если используются в сценарии.  
Читают: `LabelResolver`.

Ключевые поля: branch/role/source_format matching, pattern/rule payload, canonical label fields, confidence/status, active flag.

Правило: отсутствие matching label rule не означает benign; событие остается unlabeled.

### `data_quality_reports`

Назначение: metadata quality/leakage/DuckDB reports.

Пишут: `DuckDBAnalyticsService.register_report()`, `DataQualityChecker`, `LeakageChecker`, smoke/e2e checks.  
Читают: readiness, audit/reporting.

Ключевые поля: `check_group`, `artifact_type`, `artifact_id`, `status`, `severity`, `report_path`, `summary_json`, `metrics_json`, `violations_json`.

`CRITICAL` используется для leakage нарушений, которые могут сделать model-ready artifact непригодным.

## Traceability chain

Полная цепочка для model-ready artifact:

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

Если любой обязательный link отсутствует, `TraceabilityService` возвращает ошибку, а readiness check помечает traceability как `FAILED`.
