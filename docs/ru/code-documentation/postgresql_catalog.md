# PostgreSQL Catalog

PostgreSQL catalog хранит metadata, статусы, связи, пути, хеши и отчеты. Большие normalized/features/model-ready таблицы в PostgreSQL не пишутся: они хранятся в Parquet.

## Зачем нужен catalog

- регистрировать identity датасетов и файлов;
- хранить file hashes и обнаруживать изменения;
- фиксировать статусы ingestion/parser run;
- хранить parser registry и schema versions;
- связывать normalized, feature и model-ready artifacts;
- регистрировать quality/leakage reports;
- обеспечивать traceability.

## Таблицы

### `datasets`

Назначение: dataset-level metadata для raw sources и split roles.

Основные поля: `id`, `name`, `slug`, `branch`, `role`, `source_group`, `description`, `dataset_version`, `source_url`, `license_name`, `is_active`, `metadata_json`.

Связи:

- `datasets.id -> dataset_files.dataset_id`;
- `datasets.id -> normalized_artifacts.dataset_id`;
- `datasets.id -> feature_artifacts.dataset_id`.

Пишут: `CatalogIngestionService` через `DatasetRepository.get_or_create_dataset`.

Читают: normalization services, traceability, repositories.

Статусы: `is_active`; `branch` в `dns, host, network, hybrid`; `role` в `TRAIN, VALIDATION, TEST, EXPERIMENTS`.

### `ingestion_runs`

Назначение: один запуск directory scanning/catalog ingestion.

Поля: `run_uid`, `root_path`, `root_path_kind`, `branch`, `role`, `started_at`, `finished_at`, `status`, counters `files_seen/new/existing/changed/failed`, `error_message`, `report_path`.

Статусы: `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`.

Пишут: `IngestionRepository`.

Читают: audit/reporting, dataset file trace.

### `dataset_files`

Назначение: catalog record для raw/sorted file.

Поля: `dataset_id`, `ingestion_run_id`, `file_path`, `relative_path`, `file_name`, `file_extension`, `source_format`, `file_size_bytes`, `file_hash_sha256`, `file_modified_at`, `role`, `branch`, `status`, parser/label/timestamp/encoding hints, `metadata_json`, `error_message`.

Статусы:

```text
DISCOVERED, REGISTERED, CHANGED, EMPTY_FILE, UNSUPPORTED_FORMAT,
READY_FOR_PARSING, PARSED, PARTIALLY_PARSED, FAILED, SKIPPED
```

Пишут:

- `CatalogIngestionService`;
- `MarkReadyService`;
- `ParserResolver.resolve_or_mark_unsupported`;
- normalization services.

Читают:

- `NormalizeFormatRunner`;
- `NormalizeAllRunner`;
- normalization services;
- traceability.

### `parser_registry`

Назначение: metadata стратегии parser.

Поля: `parser_name`, `parser_version`, `branch`, `source_format`, `supported_role`, `normalized_schema_name`, `normalized_schema_version`, `parser_module`, `parser_class`, `priority`, `is_active`, `supports_streaming`, `requires_external_tools`, `external_tools_json`, `config_json`.

Пишут: `ParserRegistrySeeder`.

Читают: `ParserResolver`, parser coverage, normalization.

Ограничение: parser class должен существовать и наследовать `BaseParser`; иначе seed отключает active row.

### `schema_versions`

Назначение: metadata версионированных schema contracts.

Поля: `schema_name`, `schema_version`, `layer`, `branch`, `schema_path`, `schema_hash_sha256`, `is_active`, `description`, `columns_json`.

Пишут: `NormalizedSchemaRegistry.register_contract`, `SchemaRepository`.

Читают: `ParserResolver.resolve_schema_version`, smoke checks, artifact registration.

Layers: `normalized`, `features`, `model_ready`.

### `parser_runs`

Назначение: одна попытка parsing/normalization для raw file.

Поля: `run_uid`, `file_id`, `parser_registry_id`, `parser_name`, `parser_version`, `schema_version_id`, `started_at`, `finished_at`, `status`, `rows_read`, `rows_parsed`, `rows_failed`, `events_emitted`, `output_parquet_path`, `error_message`, `warning_count`, `metadata_json`, `report_path`.

Статусы: `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`.

Пишут: DNS/Host normalization services через `ParserRepository`.

Читают: `TraceabilityService`, artifact repositories, reports.

### `normalized_artifacts`

Назначение: registry row для normalized Parquet output.

Поля: `artifact_uid`, `dataset_id`, `file_id`, `parser_run_id`, `schema_version_id`, `role`, `branch`, `modality`, `source_format`, `normalized_path`, `schema_name`, `schema_version`, `row_count`, `event_count`, `file_size_bytes`, `content_hash_sha256`, status, timestamp и label distributions, `metadata_json`.

Статусы: `PENDING`, `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED`.

Пишут: `ParquetArtifactWriter.register_normalized_artifact`.

Читают: feature writer, traceability, DuckDB via Parquet path.

### `feature_artifacts`

Назначение: registry row для feature Parquet output.

Поля: `artifact_uid`, `dataset_id`, `normalized_artifact_id`, `role`, `branch`, `feature_group`, `feature_path`, schema name/version, row/sample/feature/entity/window counts, label distribution, excluded columns, status, metadata.

Пишут: `FeatureArtifactWriter`.

Читают: model-ready registry, preprocessing registry, traceability.

### `preprocessing_artifacts`

Назначение: metadata для scaler/encoder/imputer/preprocessing object.

Поля: `artifact_uid`, `branch`, `feature_group`, `preprocessing_type`, `artifact_path`, `fitted_on_role`, `fitted_on_feature_artifact_id`, schema/object versions, columns/params JSON, status.

DB constraint: `fitted_on_role = 'TRAIN'`.

Пишут: `ModelReadyRegistryService.register_preprocessing_artifact`.

Читают: `LeakageChecker._preprocessing_fit_role_check`, model-ready artifacts.

### `model_ready_artifacts`

Назначение: final metadata для model-ready X/y/sequence/split/preprocessing.

Поля: `artifact_uid`, `feature_artifact_id`, `preprocessing_artifact_id`, `role`, `branch`, `data_type`, `artifact_path`, schema name/version, sample/feature counts, label distribution, excluded columns, sequence length, status, metadata.

Data types: `X`, `y`, `sequence`, `split_index`, `preprocessing_metadata`.

Пишут: `ModelReadyRegistryService`.

Читают: `LeakageChecker`, `TraceabilityService`, DuckDB views.

### `label_mapping_rules`

Назначение: explainable rules для назначения labels.

Поля: `rule_uid`, `rule_name`, `branch`, `role`, `source_format`, `dataset_name_pattern`, `file_name_pattern`, `source_field`, `source_value_pattern`, canonical label fields, `priority`, `is_active`, `description`.

Пишут: manual seed/config или repository.

Читают: `LabelResolver` через `LabelRepository.find_matching_rules`.

### `data_quality_reports`

Назначение: registry для quality/leakage/schema reports.

Поля: `report_uid`, `artifact_type`, `artifact_id`, `check_group`, `check_name`, `status`, `severity`, row counters, missing/duplicate/schema/leakage counts, label/timestamp distributions, `details_json`, `report_path`.

Значения статуса: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED`.

Severity values: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

Пишут:

- `DuckDBAnalyticsService.register_report`;
- `register_quality_report`.

Читают: audit/reporting/CI gating.

## Traceability chain

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

`TraceabilityService` требует наличие каждого link. `feature_artifacts.normalized_artifact_id` и `model_ready_artifacts.feature_artifact_id` nullable в schema, поэтому production model-ready artifact должен заполнять эти поля, иначе traceability будет неполной.

## Почему не хранить большие таблицы в PostgreSQL

- normalized/events/features/model-ready rows могут быть на сотни тысяч или миллионы строк;
- PostgreSQL catalog нужен для metadata и lineage, а не для аналитического сканирования больших columnar datasets;
- Parquet + DuckDB дают columnar storage и SQL-проверки без перегрузки catalog DB;
- backups catalog metadata остаются компактными.
