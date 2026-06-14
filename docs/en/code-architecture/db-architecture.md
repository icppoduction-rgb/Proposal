# PostgreSQL Catalog and SQLAlchemy Layer

## Purpose

`scripts/db` contains the PostgreSQL Catalog infrastructure for Stage Two. The catalog stores metadata for datasets, raw files, parser registry, schema versions, parser runs, normalized/features/model-ready artifacts, label rules, and quality reports. Large payloads are not stored in PostgreSQL; they remain in raw files and Parquet storage.

## Components

| Path | Purpose |
|---|---|
| `scripts/db/config.py` | Loads `DATABASE_URL` and SQLAlchemy settings from the environment. |
| `scripts/db/session.py` | Creates engine/session factory and `session_scope()`. |
| `scripts/db/smoke_check.py` | DB connectivity/health check. |
| `scripts/db/models/*` | SQLAlchemy ORM models. |
| `scripts/db/repositories/*` | Repository API for Stage Two services. |
| `scripts/db/migrations` | Alembic environment and migration `5a38996dff5f_create_stage_two_catalog_schema.py`. |

## ORM Tables

| Table | Model | Purpose |
|---|---|---|
| `datasets` | `Dataset` | Dataset-level metadata: name, slug, branch, role, source group, version, license, metadata_json. |
| `ingestion_runs` | `IngestionRun` | Catalog ingestion runs: root path, status, counters, started/finished timestamps. |
| `dataset_files` | `DatasetFile` | One raw file: path, extension, source_format, hash, role, branch, status, parser hints, metadata. |
| `parser_registry` | `ParserRegistry` | Available parser strategies: parser name/version/class/module, branch, source_format, role, priority, active flag. |
| `schema_versions` | `SchemaVersion` | Versioned schemas for normalized/features/model-ready layers. Stage Two seed must create the normalized schema entry. |
| `parser_runs` | `ParserRun` | Parser execution for one raw file: parser, schema, status, counters, errors. |
| `normalized_artifacts` | `NormalizedArtifact` | References to normalized Parquet artifacts and schema version. |
| `feature_artifacts` | `FeatureArtifact` | References to feature Parquet artifacts, feature schema, counters, excluded columns. |
| `preprocessing_artifacts` | `PreprocessingArtifact` | Fitted preprocessing artifacts and their links to feature/model-ready layers. |
| `model_ready_artifacts` | `ModelReadyArtifact` | Final model-ready artifacts, data type, schema, counters, label distribution. |
| `label_mapping_rules` | `LabelMappingRule` | Label mapping rules for branch/source/dataset/format. |
| `data_quality_reports` | `DataQualityReport` | DuckDB/leakage/readiness check reports and their details_json. |

## Constraints and Statuses

Models use check constraints for roles, branches, statuses, and layer/data_type values. Main domains are defined in `scripts/db/models/constants.py`.

| Domain | Usage |
|---|---|
| `BRANCH_VALUES` | `dns`, `host`, `network`, `hybrid` in catalog/artifacts/parser registry. |
| `ROLE_VALUES` | `TRAIN`, `VALIDATION`, `TEST`. |
| `FILE_STATUS_VALUES` | Raw file statuses, including `REGISTERED`, `READY_FOR_PARSING`, unsupported/changed/error states. |
| `RUN_STATUS_VALUES` | Parser/artifact/check run statuses. |
| `SCHEMA_LAYER_VALUES` | `normalized`, `features`, `model_ready`. |

## Repositories

| Repository | Purpose |
|---|---|
| `BaseRepository` | Shared CRUD helpers. |
| `DatasetRepository` | Upsert/lookup datasets. |
| `DatasetFileRepository` | Upsert/lookup raw files, `get_files_ready_for_parsing(branch, limit)`. |
| `IngestionRepository` | Register ingestion runs and counters. |
| `ParserRepository` | Parser registry lookup and parser run/artifact registration. |
| `SchemaRepository` | Upsert/lookup schema_versions. |
| `ArtifactRepository` | Register normalized/feature/model-ready artifacts. |
| `PreprocessingRepository` | Register preprocessing artifacts. |
| `LabelRepository` | Label mapping rules. |
| `DataQualityRepository` | Register quality reports. |

## Session Lifecycle

Stage Two services use `session_scope()`:

```text
with session_scope() as session:
    repository = DatasetFileRepository(session)
    ...
```

The context manager handles commit/rollback/close. Stage Two CLI commands open a session for the operation and pass it to service/repository layers.

## Relation to Stage Two

| Stage Two step | Tables |
|---|---|
| `catalog-ingest` | `ingestion_runs`, `datasets`, `dataset_files` |
| `seed-parser-registry` | `schema_versions`, `parser_registry` |
| `normalize-dns` / `normalize-host` | `dataset_files`, `parser_registry`, `schema_versions`, `parser_runs`, `normalized_artifacts` |
| `run-duckdb-checks` / `run-leakage-checks` | `data_quality_reports` |
| feature/model-ready APIs | `feature_artifacts`, `preprocessing_artifacts`, `model_ready_artifacts` |
| `trace-artifact` | Read path across artifact tables back to `dataset_files` |

## Development Rules

- Every new normalized schema must be registered in `schema_versions`; parser registry entries must reference schema name/version.
- Planned/unsupported parsers must not have `is_active=true`.
- PostgreSQL stores metadata and traceability, not event rows.
- Do not create Parquet outputs without registering catalog artifacts if traceability is required.
