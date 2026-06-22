# PostgreSQL Catalog and SQLAlchemy Layer

PostgreSQL Catalog stores Stage Two metadata, statuses, relationships, paths, hashes, and reports. Large normalized/features/model-ready tables are not written to PostgreSQL: they are stored as Parquet under `PATH_DATA_STORAGE`, while the catalog stores references and aggregated metadata.

## Code Locations

| Component | Path |
| --- | --- |
| DB settings | `scripts/db/config.py` |
| Engine/session | `scripts/db/session.py` |
| Models | `scripts/db/models/*` |
| Constants/status values | `scripts/db/models/constants.py` |
| Repositories | `scripts/db/repositories/*` |
| Alembic migrations | `scripts/db/migrations/*` |
| Smoke check | `scripts/db/smoke_check.py` |

`session_scope()` creates a SQLAlchemy session, commits on successful exit, and rolls back on exceptions.

## Migrations and Smoke Check

```bash
alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m scripts.db.smoke_check
```

The smoke check creates temporary records inside a transaction and verifies:

- unique/check constraints;
- creation of `datasets`, `ingestion_runs`, `dataset_files`;
- parser run lifecycle;
- registration of normalized, feature, preprocessing, model-ready artifacts;
- rejection of `TEST` for preprocessing fit;
- quality report registration.

## Core Constraints

| Constraint group | Values |
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

The Stage Two catalog scanner activates only `TRAIN`, `VALIDATION`, and `TEST`. `EXPERIMENTS` exists as a DB-compatible value, but it must not enter the main normalization pipeline.

## Tables

### `datasets`

Purpose: logical group of files for one dataset/branch/role/source group.

Written by: `CatalogIngestionService`, DB smoke check.  
Read by: normalization services, artifact registration, readiness checks.

Key fields: `id`, `name`, `slug`, `branch`, `role`, `source_group`, `root_path`, timestamps/metadata.

Relationships: `datasets.id -> dataset_files.dataset_id`, `normalized_artifacts.dataset_id`, `feature_artifacts.dataset_id`.

### `ingestion_runs`

Purpose: one scan of an input tree.

Written by: `CatalogIngestionService`.  
Read by: diagnostics/readiness.

Key fields: `id`, `root_path`, `root_path_kind`, `branch`, `role`, counters, `status`, timestamps, error fields.

### `dataset_files`

Purpose: raw/input file metadata, including path, size, hash, role, branch, source format, and lifecycle status.

Written by: catalog ingestion, large-file splitter with `--register`, status tools.  
Read by: parser resolver, normalization runners/services, readiness raw hash check.

Key fields: `dataset_id`, `ingestion_run_id`, `file_path`, `relative_path`, `file_name`, `file_extension`, `source_format`, `file_size_bytes`, `file_hash_sha256`, `role`, `branch`, `status`, `error_message`, `metadata_json`.

Statuses: `REGISTERED` after ingestion, `READY_FOR_PARSING` after `mark-ready`, `PARSED`/`PARTIALLY_PARSED`/`FAILED` after normalization, `UNSUPPORTED_FORMAT` when no parser exists.

### `parser_registry`

Purpose: declarative registry of parser implementations.

Written by: `ParserRegistrySeeder`.  
Read by: `ParserResolver`, normalization services, parser coverage, readiness.

Key fields: `parser_name`, `parser_version`, `branch`, `source_format`, `supported_role`, `priority`, `normalized_schema_name`, `normalized_schema_version`, `parser_module`, `parser_class`, `is_active`, `config_json`.

The resolver selects an active parser by `branch/source_format`, a role-specific entry or `supported_role IS NULL`, then sorts by `priority` and `id`.

### `schema_versions`

Purpose: catalog registry of schema contracts.

Written by: parser registry seed, repositories/smoke.  
Read by: parser runs, readiness, normalization.

Key fields: `schema_name`, `schema_version`, `layer`, `branch`, `schema_path`, `schema_hash_sha256`, `is_active`.

### `parser_runs`

Purpose: one parser execution for one `dataset_files.id`.

Written by: DNS/Host normalization services.  
Read by: artifact registration, traceability, readiness.

Key fields: `file_id`, `parser_registry_id`, `schema_version_id`, `parser_name`, `parser_version`, `status`, counters (`rows_read`, `rows_parsed`, `rows_failed`, `events_emitted`), `output_parquet_path`, error samples/timestamps.

Statuses: `RUNNING`, then `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, or `SKIPPED`.

### `normalized_artifacts`

Purpose: metadata for a normalized Parquet artifact.

Written by: `ParquetArtifactWriter.register_normalized_artifact()`.  
Read by: feature writer/registry services, DuckDB/readiness, traceability.

Key fields: `dataset_id`, `file_id`, `parser_run_id`, `schema_version_id`, `role`, `branch`, `modality`, `source_format`, `normalized_path`, `schema_name`, `schema_version`, `row_count`, `event_count`, `file_size_bytes`, `content_hash_sha256`, `status`.

### `feature_artifacts`

Purpose: metadata for a feature Parquet artifact.

Written by: `FeatureArtifactWriter.write_and_register()`.  
Read by: model-ready registry, leakage checks, readiness, traceability.

Key fields: `dataset_id`, `normalized_artifact_id`, `role`, `branch`, `feature_group`, `feature_path`, `feature_schema_name`, `feature_schema_version`, `row_count`, `sample_count`, `feature_count`, `excluded_columns_json`, `label_distribution_json`, `status`.

For production traceability, `normalized_artifact_id` must be populated. Readiness check treats an artifact without this link as an error.

### `preprocessing_artifacts`

Purpose: metadata for scaler/encoder/other preprocessing objects.

Written by: `ModelReadyRegistryService.register_preprocessing_artifact()`.  
Read by: model-ready registry, leakage checks/readiness.

Key fields: `branch`, `feature_group`, `preprocessing_type`, `artifact_path`, `fitted_on_role`, `fitted_on_feature_artifact_id`, `schema_version`, `object_version`, `columns_json`, `params_json`, `status`.

Constraint: `fitted_on_role` must be `TRAIN`. The code rejects `TEST`.

### `model_ready_artifacts`

Purpose: metadata for model-ready X/y/sequence/split/preprocessing tables or files.

Written by: `ModelReadyRegistryService.write_table_artifact()` and `register_external_artifact()`.  
Read by: leakage checks, traceability, readiness.

Key fields: `feature_artifact_id`, `preprocessing_artifact_id`, `role`, `branch`, `data_type`, `artifact_path`, `schema_name`, `schema_version`, `sample_count`, `feature_count`, `excluded_columns_json`, `label_distribution_json`, `sequence_length`, `status`.

`data_type` supports `X`, `y`, `sequence`, `split_index`, and `preprocessing_metadata`. For `X`, the registry validates forbidden leakage columns.

### `label_mapping_rules`

Purpose: explicit/external rules for the label resolver.

Written by: `LabelRepository` or configuration loaders when used by the scenario.  
Read by: `LabelResolver`.

Key fields: branch/role/source_format matching, pattern/rule payload, canonical label fields, confidence/status, active flag.

Rule: absence of a matching label rule does not mean benign; the event remains unlabeled.

### `data_quality_reports`

Purpose: metadata for quality/leakage/DuckDB reports.

Written by: `DuckDBAnalyticsService.register_report()`, `DataQualityChecker`, `LeakageChecker`, smoke/e2e checks.  
Read by: readiness, audit/reporting.

Key fields: `check_group`, `artifact_type`, `artifact_id`, `status`, `severity`, `report_path`, `summary_json`, `metrics_json`, `violations_json`.

`CRITICAL` is used for leakage violations that can make a model-ready artifact unusable.

## Traceability Chain

Full chain for a model-ready artifact:

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

If any required link is missing, `TraceabilityService` returns an error and readiness check marks traceability as `FAILED`.
