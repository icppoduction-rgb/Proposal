# Data Quality Checks

Stage Two quality checks validate that generated artifacts and catalog rows are usable by downstream stages.

## Commands

```powershell
python manage.py stage-two run-duckdb-checks
python -m scripts.stage_two.readiness_check
```

## DuckDB Checks

`run-duckdb-checks` is implemented by `DuckDBAnalyticsService`.

It verifies that:

- DuckDB can create views over Parquet locations.
- Required normalized/model-ready columns are present where applicable.
- Empty buckets do not crash view creation.
- Reports can be registered in PostgreSQL.

Expected successful output:

```text
"service": "stage-two run-duckdb-checks"
"status": "SUCCESS"
"check_count": <number>
```

## Readiness Check

`scripts.stage_two.readiness_check` validates:

| Check | Purpose |
| --- | --- |
| `storage_paths` | Required `PATH_DATA_STORAGE` paths exist. |
| `migrations` | Alembic head is applied. |
| `catalog_counts` | Required catalog tables are not unexpectedly empty. |
| `schema_versions` | Normalized schema version is registered. |
| `normalized_artifacts` | Normalized artifact statuses are valid. |
| `artifact_registration` | Artifact relationships are intact. |
| `parser_coverage` | Catalog files have parser coverage. |
| `quality_leakage_reports` | Quality/leakage reports exist and no critical leakage is present. |
| `raw_files` | Catalog file hashes still match raw files. |
| `traceability` | Raw -> parser run -> normalized -> feature -> model-ready chain can be traversed when rows exist. |

Readiness reports:

```text
reports/en/stage-two/stage_two_readiness_report.json
reports/en/stage-two/stage_two_readiness_report.md
reports/ru/stage-two/stage_two_readiness_report.md
```

## Parser Smoke Checks

Use these before accepting parser changes:

```powershell
python -m scripts.stage_two.parser_smoke
python -m scripts.stage_two.parser_input_smoke
python -m scripts.stage_two.parser_catalog_smoke
python -m scripts.stage_two.cli_operational_smoke
```

| Smoke | What it validates |
| --- | --- |
| `parser_smoke` | One direct parser smoke per parser group. |
| `parser_input_smoke` | Base64, encodings, gzip, negative base64 cases, raw hash preservation. |
| `parser_catalog_smoke` | Registry -> catalog ingestion -> mark-ready -> normalization -> Parquet -> catalog artifact registration with rollback. |
| `cli_operational_smoke` | CLI workflow, old aliases, dry-run/apply semantics, normalize-format scope, normalize-all grouping. |

## Typical Failures

| Failure | Meaning | Fix |
| --- | --- | --- |
| missing storage path | `bootstrap-storage` has not been run or `PATH_DATA_STORAGE` is wrong. | Configure path and run bootstrap. |
| missing schema version | Parser registry seed was not run. | Run `seed-parser-registry`. |
| parser coverage gap | Catalog has format without active parser. | Add registry/parser or fix scanner inference. |
| raw hash mismatch | Raw file changed after catalog ingestion. | Re-ingest catalog and review `CHANGED` status. |
| traceability failure | Artifact relationships are incomplete. | Inspect parser run and artifact registration code. |
