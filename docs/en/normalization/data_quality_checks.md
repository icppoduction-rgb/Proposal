# Data Quality Checks

Stage Two uses two check layers:

1. DuckDB analytics checks over Parquet views.
2. `DataQualityChecker`/`LeakageChecker` with registration in `data_quality_reports`.

## DuckDB Analytics

Command:

```bash
python manage.py stage-two run-duckdb-checks
```

Code:

```text
scripts/stage_two/duckdb/service.py
```

Checks:

- views `normalized_all`, `features_all`, `model_ready_all` can be created;
- row counts by Parquet layer;
- required columns;
- split contamination;
- schema mismatch.

Report:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

After registration in catalog, a `data_quality_reports` row is created for DuckDB/quality diagnostics.

## DataQualityChecker

Code:

```text
scripts/stage_two/quality/checkers.py
```

`DataQualityChecker` reads DuckDB views and checks:

| Check | Purpose |
| --- | --- |
| Required columns | Contract columns exist in views. |
| Null counts | Visibility into null values in critical columns. |
| Duplicate keys | Duplicate key event/sample identifiers. |
| Role domain | `role`/`dataset_role` values are restricted to `TRAIN`, `VALIDATION`, `TEST`. |
| Branch domain | `branch` values are restricted to catalog constants. |

Reports are written to EN/RU report roots and can be registered through `DataQualityRepository`.

## Severity Levels

| Severity | Meaning |
| --- | --- |
| `INFO` | Diagnostic information. |
| `WARNING` | Undesirable state that does not always block the pipeline. |
| `ERROR` | Contract or data quality violation. |
| `CRITICAL` | Violation that can cause leakage, split mixing, or unreliable model-ready artifacts. |

## Relationship to Leakage Checks

`LeakageChecker` is implemented in the same module but documented separately in [data_leakage_prevention.md](data_leakage_prevention.md). Its CRITICAL results are also registered in `data_quality_reports`, usually with `check_group = "leakage"`.

## Readiness Check

```bash
python -m scripts.stage_two.readiness_check
```

Readiness verifies that:

- migrations are applied;
- storage paths exist;
- catalog contains datasets/files/parser_registry/schema_versions/artifacts/reports;
- parser coverage has no uncovered combinations;
- normalized artifacts exist and are not failed;
- feature/model-ready artifacts are linked to upstream artifacts;
- quality/leakage reports exist;
- traceability chain can be reconstructed;
- raw file hashes match the catalog.

Readiness reports are saved to:

```text
reports/en/stage-two/stage_two_readiness_report.md
reports/ru/stage-two/stage_two_readiness_report.md
reports/en/stage-two/stage_two_readiness_report.json
```

## Blocking Conditions

Blocking scenarios:

- `TEST` appears in preprocessing fit/training context;
- label/source fields appear in model-ready `X`;
- a required traceability link is missing;
- raw file hash does not match the catalog;
- parser coverage is missing for files that should be normalized;
- role contamination between `TRAIN`, `VALIDATION`, and `TEST`.

These violations must be fixed before artifacts are used in ML experiments.
