# Database Architecture

Database code lives under `scripts/db/`.

## Files

| Path | Purpose |
| --- | --- |
| `scripts/db/config.py` | Database URL and SQLAlchemy config helpers. |
| `scripts/db/session.py` | Engine/session factory and `session_scope()`. |
| `scripts/db/models/` | SQLAlchemy ORM models. |
| `scripts/db/repositories/` | Repository layer for catalog operations. |
| `scripts/db/migrations/` | Alembic configuration and migrations. |
| `scripts/db/smoke_check.py` | DB foundation smoke checks. |

## Transaction Pattern

CLI commands use:

```python
from scripts.db import session_scope

with session_scope() as session:
    ...
```

Batch normalization uses nested transactions per file so one bad file does not abort the whole batch.

## Alembic

Commands:

```powershell
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m alembic -c scripts/db/migrations/alembic.ini current
```

Current migration head:

```text
5a38996dff5f
```

## Smoke Check

```powershell
python -m scripts.db.smoke_check
```

The smoke validates:

- dataset creation;
- unique/check constraints;
- ingestion run creation;
- dataset file creation;
- parser run creation;
- normalized artifact creation;
- TRAIN-only preprocessing artifact rule;
- data quality report creation;
- rollback behavior.

## Repository Responsibilities

| Repository | Responsibility |
| --- | --- |
| `DatasetRepository` | Dataset lookup and creation. |
| `DatasetFileRepository` | File status updates, ready-file queries, grouping. |
| `IngestionRepository` | Ingestion run records. |
| `ParserRepository` | Parser registry rows and parser runs. |
| `SchemaRepository` | Schema version records. |
| `ArtifactRepository` | Normalized, feature, model-ready artifact registration. |
| `PreprocessingRepository` | Preprocessing artifact metadata. |
| `LabelRepository` | Label mapping rules. |
| `DataQualityRepository` | Quality/leakage/readiness report rows. |

## Catalog Tables

| Table | Model | Purpose |
| --- | --- | --- |
| `datasets` | `Dataset` | Dataset metadata: name, slug, branch, role, source group, version, license, metadata. |
| `ingestion_runs` | `IngestionRun` | Catalog ingestion run metadata, counters, status, timestamps. |
| `dataset_files` | `DatasetFile` | One raw file with path, relative path, extension, source_format, branch, role, hash, size, status, parser hints. |
| `parser_registry` | `ParserRegistry` | Parser strategy metadata: branch, role, source_format, module/class, parser name/version, priority, active flag. |
| `schema_versions` | `SchemaVersion` | Versioned schema contracts for normalized/features/model_ready layers. |
| `parser_runs` | `ParserRun` | Parser execution for one file: parser, schema, status, counters, report path, errors. |
| `normalized_artifacts` | `NormalizedArtifact` | Normalized Parquet artifact path/hash/row count/schema/parser run metadata. |
| `feature_artifacts` | `FeatureArtifact` | Feature Parquet artifact metadata. |
| `preprocessing_artifacts` | `PreprocessingArtifact` | Fitted preprocessing artifact metadata. |
| `model_ready_artifacts` | `ModelReadyArtifact` | Model-ready artifact metadata. |
| `label_mapping_rules` | `LabelMappingRule` | Safe label mapping rules. |
| `data_quality_reports` | `DataQualityReport` | DuckDB/leakage/readiness report metadata and details. |

## Command To Table Mapping

| Command | Main tables |
| --- | --- |
| `catalog-ingest` | `ingestion_runs`, `datasets`, `dataset_files` |
| `seed-parser-registry` | `schema_versions`, `parser_registry` |
| `parser-coverage` | reads `dataset_files`, `parser_registry`, `schema_versions`; writes report files |
| `mark-ready` | updates `dataset_files.status` |
| `normalize-format` / `normalize-all` | reads catalog/registry/schema; writes `parser_runs`, `normalized_artifacts`; updates file status |
| `run-duckdb-checks` / `run-leakage-checks` | writes `data_quality_reports` |

## Data Storage Boundary

PostgreSQL stores control-plane metadata. Parquet stores large row data. Do not add payload tables for normalized events, packet payloads, BSON streams, or raw logs.
