# Data Quality Checks

The quality layer is implemented in `scripts/stage_two/quality/checkers.py`.

## DuckDB Checks

Command:

```powershell
python manage.py stage-two run-duckdb-checks
```

Checks:

- row counts by role/branch when such columns are available;
- required columns in `normalized_all`, `features_all`, and `model_ready_all`;
- split contamination rule for model-ready data;
- schema mismatch summary.

The report is saved to:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/duckdb_analytics_report.json
```

and registered in `data_quality_reports`.

## DataQualityChecker

`DataQualityChecker` also checks:

- required columns;
- null counts for required columns;
- duplicate keys for `event_uid`/`sample_uid` when present;
- allowed role and branch values.

Reports are saved in RU and EN:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/quality_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/quality/quality_report.json
```

## Severity

- Successful checks use `INFO`.
- Quality failures use `ERROR`.
- Leakage checks use `CRITICAL` on failure.

## Catalog Registration

Aggregate results are stored in `data_quality_reports` with:

- `artifact_type`
- `check_group`
- `check_name`
- `status`
- `severity`
- row counters
- mismatch/leakage counters
- `report_path`
- `details_json`
