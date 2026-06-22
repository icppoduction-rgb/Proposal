# Stage Two Normalization Final Summary Template

Use this template after changing the parser/normalization pipeline or after a complete Stage Two run.

## Run Scope

- Branches:
- Roles:
- Source formats:
- Storage root:
- Catalog DB:
- Code revision:

## Commands

```bash
python manage.py stage-two bootstrap-storage
alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --apply
python manage.py stage-two normalize-format --branch <branch> --role <ROLE> --format <format> --limit <N>
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

## Catalog Summary

| Table | Count | Notes |
| --- | ---: | --- |
| `datasets` |  |  |
| `ingestion_runs` |  |  |
| `dataset_files` |  |  |
| `parser_registry` |  |  |
| `parser_runs` |  |  |
| `normalized_artifacts` |  |  |
| `feature_artifacts` |  |  |
| `model_ready_artifacts` |  |  |
| `data_quality_reports` |  |  |

## Parser Coverage

| Branch | Role | Source format | Parser | Status | Notes |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Normalization Results

| Branch | Role | Source format | Files | Parsed | Partial | Failed | Unsupported |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
|  |  |  |  |  |  |  |  |

## Quality and Leakage

| Check group | Status | Severity | Report path | Notes |
| --- | --- | --- | --- | --- |
| DuckDB analytics |  |  |  |  |
| Data quality |  |  |  |  |
| Leakage |  |  |  |  |
| Readiness |  |  |  |  |

## Traceability Sample

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

Checked artifact:

- model_ready_artifact:
- feature_artifact:
- normalized_artifact:
- parser_run:
- dataset_file:
- dataset:

## Limitations and Follow-Up

- Unsupported formats:
- Parser gaps:
- Label risks:
- Timestamp risks:
- Large-file risks:
- Schema drift:
- Required next actions:
