# Data quality checks

Stage Two quality checks проверяют, что generated artifacts и catalog rows пригодны для downstream stages.

## Commands

```powershell
python manage.py stage-two run-duckdb-checks
python -m scripts.stage_two.readiness_check
```

## DuckDB checks

`run-duckdb-checks` реализован в `DuckDBAnalyticsService`.

Проверяет:

- DuckDB может создать views поверх Parquet locations.
- Required normalized/model-ready columns присутствуют там, где применимо.
- Empty buckets не ломают view creation.
- Reports регистрируются в PostgreSQL.

Expected successful output:

```text
"service": "stage-two run-duckdb-checks"
"status": "SUCCESS"
"check_count": <number>
```

## Readiness check

`scripts.stage_two.readiness_check` проверяет:

| Check | Purpose |
| --- | --- |
| `storage_paths` | Required `PATH_DATA_STORAGE` paths exist. |
| `migrations` | Alembic head applied. |
| `catalog_counts` | Required catalog tables not unexpectedly empty. |
| `schema_versions` | Normalized schema version registered. |
| `normalized_artifacts` | Normalized artifact statuses valid. |
| `artifact_registration` | Artifact relationships intact. |
| `parser_coverage` | Catalog files have parser coverage. |
| `quality_leakage_reports` | Quality/leakage reports exist and no critical leakage. |
| `raw_files` | Catalog file hashes still match raw files. |
| `traceability` | Raw -> parser run -> normalized -> feature -> model-ready chain traversable when rows exist. |

Readiness reports:

```text
reports/en/stage-two/stage_two_readiness_report.json
reports/en/stage-two/stage_two_readiness_report.md
reports/ru/stage-two/stage_two_readiness_report.md
```

## Parser smoke checks

Перед acceptance parser changes:

```powershell
python -m scripts.stage_two.parser_smoke
python -m scripts.stage_two.parser_input_smoke
python -m scripts.stage_two.parser_catalog_smoke
python -m scripts.stage_two.cli_operational_smoke
```

| Smoke | Что проверяет |
| --- | --- |
| `parser_smoke` | One direct parser smoke per parser group. |
| `parser_input_smoke` | Base64, encodings, gzip, negative base64 cases, raw hash preservation. |
| `parser_catalog_smoke` | Registry -> catalog ingestion -> mark-ready -> normalization -> Parquet -> catalog artifact registration with rollback. |
| `cli_operational_smoke` | CLI workflow, old aliases, dry-run/apply semantics, normalize-format scope, normalize-all grouping. |

## Typical failures

| Failure | Meaning | Fix |
| --- | --- | --- |
| missing storage path | `bootstrap-storage` не запускался или `PATH_DATA_STORAGE` wrong. | Configure path and run bootstrap. |
| missing schema version | Parser registry seed не запускался. | Run `seed-parser-registry`. |
| parser coverage gap | Catalog имеет format без active parser. | Add registry/parser or fix scanner inference. |
| raw hash mismatch | Raw file changed after catalog ingestion. | Re-ingest catalog and review `CHANGED` status. |
| traceability failure | Artifact relationships incomplete. | Inspect parser run and artifact registration code. |
