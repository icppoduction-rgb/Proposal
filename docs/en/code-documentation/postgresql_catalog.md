# PostgreSQL Catalog

PostgreSQL Catalog stores metadata, statuses, links, paths, hashes, and reports. Large normalized/features/model-ready tables are not stored in PostgreSQL; they are stored as Parquet artifacts.

## Why the Catalog Exists

- register dataset and file identity;
- store file hashes and detect changes;
- record ingestion/parser run statuses;
- store parser registry and schema versions;
- link normalized, feature, and model-ready artifacts;
- register quality/leakage reports;
- support traceability.

## Tables

### `datasets`

Purpose: dataset-level metadata for raw sources and split roles.

Main fields: `id`, `name`, `slug`, `branch`, `role`, `source_group`, `description`, `dataset_version`, `source_url`, `license_name`, `is_active`, `metadata_json`.

Relationships:

- `datasets.id -> dataset_files.dataset_id`;
- `datasets.id -> normalized_artifacts.dataset_id`;
- `datasets.id -> feature_artifacts.dataset_id`.

Written by: `CatalogIngestionService` through `DatasetRepository.get_or_create_dataset`.

Read by: normalization services, traceability, repositories.

### `ingestion_runs`

Purpose: one directory scanning/catalog ingestion run.

Fields: `run_uid`, `root_path`, `root_path_kind`, `branch`, `role`, `started_at`, `finished_at`, `status`, counters `files_seen/new/existing/changed/failed`, `error_message`, `report_path`.

Statuses: `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`.

Written by: `IngestionRepository`.

Read by: audit/reporting and dataset file tracing.

### `dataset_files`

Purpose: catalog record for one raw/sorted file.

Fields: `dataset_id`, `ingestion_run_id`, `file_path`, `relative_path`, `file_name`, `file_extension`, `source_format`, `file_size_bytes`, `file_hash_sha256`, `file_modified_at`, `role`, `branch`, `status`, parser/label/timestamp/encoding hints, `metadata_json`, `error_message`.

Statuses:

```text
DISCOVERED, REGISTERED, CHANGED, EMPTY_FILE, UNSUPPORTED_FORMAT,
READY_FOR_PARSING, PARSED, PARTIALLY_PARSED, FAILED, SKIPPED
```

Written by:

- `CatalogIngestionService`;
- `MarkReadyService`;
- `ParserResolver.resolve_or_mark_unsupported`;
- normalization services.

Read by normalization runners and traceability.

### `parser_registry`

Purpose: parser strategy metadata.

Fields: `parser_name`, `parser_version`, `branch`, `source_format`, `supported_role`, `normalized_schema_name`, `normalized_schema_version`, `parser_module`, `parser_class`, `priority`, `is_active`, `supports_streaming`, `requires_external_tools`, `external_tools_json`, `config_json`.

Written by: `ParserRegistrySeeder`.

Read by: `ParserResolver`, parser coverage, normalization.

Constraint: parser class must exist and inherit `BaseParser`; otherwise seed disables the active row.

### `schema_versions`

Purpose: versioned schema contract metadata.

Fields: `schema_name`, `schema_version`, `layer`, `branch`, `schema_path`, `schema_hash_sha256`, `is_active`, `description`, `columns_json`.

Written by: `NormalizedSchemaRegistry.register_contract`, `SchemaRepository`.

Read by: `ParserResolver.resolve_schema_version`, smoke checks, artifact registration.

Layers: `normalized`, `features`, `model_ready`.

### `parser_runs`

Purpose: one parsing/normalization attempt for a raw file.

Fields: `run_uid`, `file_id`, `parser_registry_id`, `parser_name`, `parser_version`, `schema_version_id`, `started_at`, `finished_at`, `status`, `rows_read`, `rows_parsed`, `rows_failed`, `events_emitted`, `output_parquet_path`, `error_message`, `warning_count`, `metadata_json`, `report_path`.

Statuses: `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`.

Written by: DNS/Host normalization services through `ParserRepository`.

Read by: `TraceabilityService`, artifact repositories, reports.

### `normalized_artifacts`

Purpose: registry row for normalized Parquet output.

Fields: `artifact_uid`, `dataset_id`, `file_id`, `parser_run_id`, `schema_version_id`, `role`, `branch`, `modality`, `source_format`, `normalized_path`, `schema_name`, `schema_version`, `row_count`, `event_count`, `file_size_bytes`, `content_hash_sha256`, status, timestamp and label distributions, `metadata_json`.

Statuses: `PENDING`, `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED`.

Written by: `ParquetArtifactWriter.register_normalized_artifact`.

Read by: feature writer, traceability, DuckDB through Parquet path.

### `feature_artifacts`

Purpose: registry row for feature Parquet output.

Fields: `artifact_uid`, `dataset_id`, `normalized_artifact_id`, `role`, `branch`, `feature_group`, `feature_path`, schema name/version, row/sample/feature/entity/window counts, label distribution, excluded columns, status, metadata.

Written by: `FeatureArtifactWriter`.

Read by: model-ready registry, preprocessing registry, traceability.

### `preprocessing_artifacts`

Purpose: metadata for scaler/encoder/imputer/preprocessing objects.

Fields: `artifact_uid`, `branch`, `feature_group`, `preprocessing_type`, `artifact_path`, `fitted_on_role`, `fitted_on_feature_artifact_id`, schema/object versions, columns/params JSON, status.

DB constraint: `fitted_on_role = 'TRAIN'`.

Written by: `ModelReadyRegistryService.register_preprocessing_artifact`.

Read by: `LeakageChecker._preprocessing_fit_role_check`, model-ready artifacts.

### `model_ready_artifacts`

Purpose: final model-ready X/y/sequence/split/preprocessing metadata.

Fields: `artifact_uid`, `feature_artifact_id`, `preprocessing_artifact_id`, `role`, `branch`, `data_type`, `artifact_path`, schema name/version, sample/feature counts, label distribution, excluded columns, sequence length, status, metadata.

Data types: `X`, `y`, `sequence`, `split_index`, `preprocessing_metadata`.

Written by: `ModelReadyRegistryService`.

Read by: `LeakageChecker`, `TraceabilityService`, DuckDB views.

### `label_mapping_rules`

Purpose: explainable rules for assigning labels.

Fields: `rule_uid`, `rule_name`, `branch`, `role`, `source_format`, `dataset_name_pattern`, `file_name_pattern`, `source_field`, `source_value_pattern`, canonical label fields, `priority`, `is_active`, `description`.

Written by: manual seed/config or repository.

Read by: `LabelResolver` through `LabelRepository.find_matching_rules`.

### `data_quality_reports`

Purpose: registry for quality/leakage/schema reports.

Fields: `report_uid`, `artifact_type`, `artifact_id`, `check_group`, `check_name`, `status`, `severity`, row counters, missing/duplicate/schema/leakage counts, label/timestamp distributions, `details_json`, `report_path`.

Status values: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED`.

Severity values: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

Written by:

- `DuckDBAnalyticsService.register_report`;
- `register_quality_report`.

Read by: audit/reporting/CI gating.

## Traceability Chain

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

`TraceabilityService` requires every link. `feature_artifacts.normalized_artifact_id` and `model_ready_artifacts.feature_artifact_id` are nullable in the schema to support staged artifacts, but production model-ready artifacts must populate them.

## Why Large Tables Stay Out of PostgreSQL

- normalized/events/features/model-ready rows can reach hundreds of thousands or millions of rows;
- PostgreSQL Catalog is for metadata and lineage, not large analytical scans;
- Parquet + DuckDB provide columnar storage and SQL checks without overloading catalog DB;
- metadata backups remain compact.
