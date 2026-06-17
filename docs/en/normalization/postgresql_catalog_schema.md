# PostgreSQL Catalog Schema

PostgreSQL is the Stage Two control plane. It stores catalog metadata, parser registry rows, parser run state, artifact records, labels, quality reports, and traceability relationships. It does not store full normalized event payloads.

The ORM models live in `scripts/db/models/`. The migration head is:

```text
5a38996dff5f_create_stage_two_catalog_schema.py
```

Check migration state:

```powershell
python -m alembic -c scripts/db/migrations/alembic.ini current
```

## Core Tables

| Table | ORM model | Purpose |
| --- | --- | --- |
| `datasets` | `Dataset` | Dataset identity: name, slug, branch, role context. |
| `ingestion_runs` | `IngestionRun` | One catalog ingestion execution and summary. |
| `dataset_files` | `DatasetFile` | Raw file catalog row with branch, role, source_format, hash, size, status. |
| `parser_registry` | `ParserRegistry` | Active/inactive parser metadata and class mapping. |
| `schema_versions` | `SchemaVersion` | Registered schema contracts, currently `normalized_event` v1 for normalized layer. |
| `parser_runs` | `ParserRun` | One parser execution for one file, with counters/status/report path. |
| `normalized_artifacts` | `NormalizedArtifact` | Registered normalized Parquet outputs. |
| `feature_artifacts` | `FeatureArtifact` | Feature artifact contract/catalog rows. |
| `model_ready_artifacts` | `ModelReadyArtifact` | Model-ready artifact contract/catalog rows. |
| `preprocessing_artifacts` | `PreprocessingArtifact` | TRAIN-fitted preprocessing object metadata. |
| `label_mapping_rules` | `LabelMappingRule` | DB-driven label mapping rules used by `LabelResolver`. |
| `data_quality_reports` | `DataQualityReport` | DuckDB, leakage, readiness, and other report metadata. |

## Main Relationships

```text
datasets.id
  -> dataset_files.dataset_id
  -> parser_runs.file_id
  -> normalized_artifacts.parser_run_id
  -> feature_artifacts.normalized_artifact_id
  -> model_ready_artifacts.feature_artifact_id
```

Traceability can be inspected with:

```powershell
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Dataset File Statuses

| Status | Meaning |
| --- | --- |
| `REGISTERED` | File was cataloged and is not yet ready for parsing. |
| `CHANGED` | Cataloged file changed and needs review. |
| `DISCOVERED` | File was discovered and can be promoted. |
| `READY_FOR_PARSING` | File is allowed to be normalized. |
| `PARSED` | Parser succeeded and wrote normalized rows. |
| `PARTIALLY_PARSED` | Parser emitted rows and recorded row-level failures. |
| `EMPTY_FILE` | File has no usable content. |
| `FAILED` | Parser or file processing failed. |
| `SKIPPED` | Helper/context file was intentionally skipped. |
| `UNSUPPORTED_FORMAT` | No active parser is available. |

Only `REGISTERED`, `CHANGED`, and `DISCOVERED` are promoted by `mark-ready`.

## Parser Runs

`parser_runs` records:

- `parser_id` and parser name/version.
- `schema_version_id` when the normalized schema is registered.
- status and row counters.
- warnings/errors summary.
- output Parquet path.
- report path.

Parser run reports are saved through `scripts/stage_two/reports/parser_reports.py`.

## Normalized Artifacts

`normalized_artifacts` records:

- dataset/file/parser run ids.
- branch, role, modality, source format.
- relative Parquet path and content hash.
- row count/event count.
- schema name/version and `schema_version_id` when available.
- artifact status.

Large event rows are in Parquet only.

## Repository Layer

Repositories in `scripts/db/repositories/` centralize writes and queries:

| Repository | Responsibility |
| --- | --- |
| `DatasetRepository` | Dataset get/create/update. |
| `DatasetFileRepository` | File status transitions and ready-file queries. |
| `ParserRepository` | Registry, parser runs, parser statuses. |
| `ArtifactRepository` | Normalized/feature/model-ready artifact registration. |
| `SchemaRepository` | Schema version registration. |
| `LabelRepository` | Label mapping rule lookup. |
| `DataQualityRepository` | Report registration. |

Use `scripts.db.session_scope()` for command-level transactions.
