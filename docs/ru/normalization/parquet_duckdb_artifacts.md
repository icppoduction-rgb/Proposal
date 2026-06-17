# Parquet and DuckDB artifacts

Stage Two пишет большие normalized данные в Parquet и использует DuckDB для SQL checks поверх Parquet outputs.

## Parquet writer

Implementation:

```text
scripts/stage_two/parquet/writer.py
```

Main methods:

| Method | Purpose |
| --- | --- |
| `write_normalized()` | Записывает normalized event rows в partitioned Parquet file. |
| `register_normalized_artifact()` | Регистрирует Parquet output в PostgreSQL `normalized_artifacts`. |

Path template:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Writer вычисляет row count, relative path и content hash.

## DuckDB analytics

Implementation:

```text
scripts/stage_two/duckdb/service.py
scripts/stage_two/duckdb/sql/create_views.sql
```

Command:

```powershell
python manage.py stage-two run-duckdb-checks
```

Service создает/обновляет views поверх normalized, feature и model-ready Parquet locations. Empty views создаются с required columns, чтобы checks не падали на пустых buckets.

## Quality report registration

DuckDB check output регистрируется через `DataQualityRepository` в `data_quality_reports` и пишется в:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/
```

Command output содержит:

```text
service: stage-two run-duckdb-checks
status: SUCCESS | FAILED
report_path: reports/en/stage-two/quality/duckdb_analytics_report.json
check_count: <number>
catalog_report_id: <id>
```

## Feature and model-ready contracts

В репозитории есть contracts для следующих pipeline stages:

```text
schemas/features/feature_artifact_v1.json
schemas/model_ready/model_ready_v1.json
scripts/stage_two/features/
scripts/stage_two/model_ready/
```

Они определяют traceability, forbidden leakage columns и expected artifact paths. Текущий Stage Two operational CLI покрывает catalog ingestion, parser normalization и checks; full-corpus production feature/model-ready build command сейчас не реализован.
