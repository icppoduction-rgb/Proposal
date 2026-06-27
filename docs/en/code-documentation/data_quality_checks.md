# Data Quality Checks

Quality code:

- `scripts/stage_two/duckdb/service.py`;
- `scripts/stage_two/quality/checks.py`;
- `scripts/stage_two/quality/checkers.py`.

## DuckDB Analytics Checks

Command:

```bash
python manage.py stage-two run-duckdb-checks
```

Checks:

| Check | Scope | Failure condition |
|---|---|---|
| `row_counts_*` | normalized/features/model-ready views | never fails; reports counts |
| `missing_required_columns_*` | each view | required columns are absent |
| `split_contamination` | `model_ready_all` | TEST rows appear in TRAIN model-ready artifacts |
| `schema_mismatch` | all views | required column mismatch |

Report:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/duckdb_analytics_report.json
```

Catalog registration:

- table: `data_quality_reports`;
- `check_group='duckdb'`;
- severity `ERROR` if any check failed, otherwise `INFO`.

## DataQualityChecker

Class: `DataQualityChecker`.

Checks:

| Check group | Details |
|---|---|
| Required columns | uses DuckDB `REQUIRED_COLUMNS` |
| Null counts | counts nulls in required columns present in each view |
| Duplicate keys | `event_uid` for normalized, `sample_uid` for features/model-ready |
| Role/branch domains | validates `role`, `dataset_role`, `branch` values |

Outputs:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/quality_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/quality/quality_report.json
```

Optional catalog registration uses `DataQualityRepository`.

Severity:

- successful checks: `INFO`;
- failed data quality checks: `ERROR`.

## LeakageChecker

Leakage details are documented in [data_leakage_prevention.md](data_leakage_prevention.md). It writes:

```text
PATH_DATA_STORAGE/reports/en/stage-two/leakage/leakage_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/leakage/leakage_report.json
```

Failed leakage report severity: `CRITICAL`.

## Report Contract

`QualityCheckResult`:

```text
check_name
status
severity
rows_total
rows_failed
details
```

`QualityReportResult`:

```text
check_group
status
severity
report_paths
checks
```

## Critical Violations

Treat as `CRITICAL`:

- label/source/leakage columns present with non-null values in model-ready X files;
- TEST rows in TRAIN model-ready artifacts;
- preprocessing artifact fitted on any role other than TRAIN.

These violations should block model-ready artifact use for training.
