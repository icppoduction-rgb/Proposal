# PostgreSQL catalog schema

PostgreSQL является Stage Two control plane. Он хранит catalog metadata, parser registry rows, parser run state, artifact records, labels, quality reports и traceability relationships. Full normalized event payloads в PostgreSQL не хранятся.

ORM models находятся в `scripts/db/models/`. Migration head:

```text
5a38996dff5f_create_stage_two_catalog_schema.py
```

Проверка migration state:

```powershell
python -m alembic -c scripts/db/migrations/alembic.ini current
```

## Core tables

| Table | ORM model | Purpose |
| --- | --- | --- |
| `datasets` | `Dataset` | Dataset identity: name, slug, branch, role context. |
| `ingestion_runs` | `IngestionRun` | Один catalog ingestion execution и summary. |
| `dataset_files` | `DatasetFile` | Raw file catalog row: branch, role, source_format, hash, size, status. |
| `parser_registry` | `ParserRegistry` | Active/inactive parser metadata и class mapping. |
| `schema_versions` | `SchemaVersion` | Registered schema contracts, сейчас `normalized_event` v1 для normalized layer. |
| `parser_runs` | `ParserRun` | Один parser execution для одного file, counters/status/report path. |
| `normalized_artifacts` | `NormalizedArtifact` | Registered normalized Parquet outputs. |
| `feature_artifacts` | `FeatureArtifact` | Feature artifact contract/catalog rows. |
| `model_ready_artifacts` | `ModelReadyArtifact` | Model-ready artifact contract/catalog rows. |
| `preprocessing_artifacts` | `PreprocessingArtifact` | TRAIN-fitted preprocessing object metadata. |
| `label_mapping_rules` | `LabelMappingRule` | DB-driven label mapping rules для `LabelResolver`. |
| `data_quality_reports` | `DataQualityReport` | DuckDB, leakage, readiness и другие report metadata. |

## Main relationships

```text
datasets.id
  -> dataset_files.dataset_id
  -> parser_runs.file_id
  -> normalized_artifacts.parser_run_id
  -> feature_artifacts.normalized_artifact_id
  -> model_ready_artifacts.feature_artifact_id
```

Traceability inspect:

```powershell
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Dataset file statuses

| Status | Meaning |
| --- | --- |
| `REGISTERED` | Файл добавлен в catalog и еще не ready for parsing. |
| `CHANGED` | Cataloged file изменился и требует review. |
| `DISCOVERED` | File discovered и может быть promoted. |
| `READY_FOR_PARSING` | File разрешен для normalization. |
| `PARSED` | Parser succeeded и записал normalized rows. |
| `PARTIALLY_PARSED` | Parser emitted rows и зафиксировал row-level failures. |
| `EMPTY_FILE` | File не имеет usable content. |
| `FAILED` | Parser или file processing failed. |
| `SKIPPED` | Helper/context file intentionally skipped. |
| `UNSUPPORTED_FORMAT` | Нет active parser. |

`mark-ready` переводит только `REGISTERED`, `CHANGED`, `DISCOVERED`.

## Parser runs

`parser_runs` хранит:

- `parser_id` и parser name/version.
- `schema_version_id`, когда normalized schema registered.
- status и row counters.
- warnings/errors summary.
- output Parquet path.
- report path.

Reports сохраняются через `scripts/stage_two/reports/parser_reports.py`.

## Normalized artifacts

`normalized_artifacts` хранит:

- dataset/file/parser run ids.
- branch, role, modality, source format.
- relative Parquet path и content hash.
- row count/event count.
- schema name/version и `schema_version_id`, если доступен.
- artifact status.

Большие event rows находятся только в Parquet.

## Repository layer

Repositories в `scripts/db/repositories/`:

| Repository | Responsibility |
| --- | --- |
| `DatasetRepository` | Dataset get/create/update. |
| `DatasetFileRepository` | File status transitions и ready-file queries. |
| `ParserRepository` | Registry, parser runs, parser statuses. |
| `ArtifactRepository` | Normalized/feature/model-ready artifact registration. |
| `SchemaRepository` | Schema version registration. |
| `LabelRepository` | Label mapping rule lookup. |
| `DataQualityRepository` | Report registration. |

Для command-level transactions используйте `scripts.db.session_scope()`.
