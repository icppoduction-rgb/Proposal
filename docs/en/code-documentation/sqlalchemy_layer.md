# SQLAlchemy Layer

## Location

```text
scripts/db/
  config.py
  session.py
  smoke_check.py
  models/
  repositories/
  migrations/
```

## Configuration

File: `scripts/db/config.py`.

`load_database_settings()` reads:

| Env | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | required | SQLAlchemy connection string |
| `SQLALCHEMY_ECHO_SQL` | `false` | SQL logging |
| `SQLALCHEMY_POOL_PRE_PING` | `true` | connection pre-ping |

If `DATABASE_URL` is missing, the function raises `ValueError`.

## Session Handling

File: `scripts/db/session.py`.

`session_scope()`:

```python
@contextmanager
def session_scope(...):
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Properties:

- commits after a successful block;
- rolls back on exception;
- always closes the session;
- uses `expire_on_commit=False`;
- uses `autoflush=False`, `autocommit=False`.

Normalization can use `session.begin_nested()` for per-file work so one failing file does not necessarily break the whole batch.

## Models

Models are stored under `scripts/db/models` and exported from `scripts/db/models/__init__.py`.

Key models:

- `Dataset`;
- `DatasetFile`;
- `IngestionRun`;
- `ParserRegistry`;
- `SchemaVersion`;
- `ParserRun`;
- `NormalizedArtifact`;
- `FeatureArtifact`;
- `PreprocessingArtifact`;
- `ModelReadyArtifact`;
- `LabelMappingRule`;
- `DataQualityReport`.

Common constants live in `scripts/db/models/constants.py`:

```text
BRANCH_VALUES = dns, host, network, hybrid
ROLE_VALUES = TRAIN, VALIDATION, TEST, EXPERIMENTS
ACTIVE_DATASET_ROLE_VALUES = TRAIN, VALIDATION, TEST
ACTIVE_CATALOG_SOURCE_GROUP = PATH_FOLDER_DATASETS_FILTER
```

## Repositories

Repositories encapsulate reads/writes and do not manage commits themselves.

| Repository | Purpose |
|---|---|
| `DatasetRepository` | get/create datasets |
| `IngestionRepository` | start/finish/fail ingestion runs |
| `DatasetFileRepository` | bulk upsert files, select ready files, update status |
| `ParserRepository` | parser registry rows and parser run lifecycle |
| `SchemaRepository` | register schema versions |
| `ArtifactRepository` | register normalized/feature/model-ready artifacts |
| `PreprocessingRepository` | register preprocessing artifacts |
| `LabelRepository` | find label mappings |
| `DataQualityRepository` | register quality/leakage reports |

`DatasetFileRepository.bulk_upsert_files()` uses PostgreSQL `ON CONFLICT` by `(dataset_id, file_path)`. If file hash changes, status becomes `CHANGED`; otherwise existing status is preserved.

## Alembic Migrations

Config: `scripts/db/migrations/alembic.ini`.

Migration:

```text
scripts/db/migrations/versions/5a38996dff5f_create_stage_two_catalog_schema.py
```

Apply:

```bash
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m alembic -c scripts/db/migrations/alembic.ini current
```

The migration creates all Stage Two catalog tables:

- `data_quality_reports`;
- `datasets`;
- `ingestion_runs`;
- `label_mapping_rules`;
- `parser_registry`;
- `schema_versions`;
- `dataset_files`;
- `parser_runs`;
- `normalized_artifacts`;
- `feature_artifacts`;
- `preprocessing_artifacts`;
- `model_ready_artifacts`.

## Smoke Check

File: `scripts/db/smoke_check.py`.

`run_smoke_checks()`:

- creates a dataset;
- checks unique/check constraints;
- creates an ingestion run;
- inserts a dataset file;
- creates parser registry/schema/parser run records;
- registers normalized, feature, preprocessing, and model-ready artifacts;
- verifies that `PreprocessingArtifact(fitted_on_role='TEST')` fails;
- creates a quality report;
- rolls back smoke data at the end.

Command:

```bash
python - <<'PY'
from scripts.db.smoke_check import run_smoke_checks
print(run_smoke_checks())
PY
```

Requires working `DATABASE_URL` and applied migrations.

## Operational Notes

- Repository methods expect a session managed externally.
- Repositories must not store large row tables in PostgreSQL.
- DB constraints protect branch/role/status domains, but do not fully prevent ML leakage. Model-ready contracts and leakage checks are still required.
