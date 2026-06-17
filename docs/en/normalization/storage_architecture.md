# Storage Architecture

Stage Two uses `PATH_DATA_STORAGE` as the root for generated data and reports. The path is configured in `config.py` from the environment.

Raw datasets stay outside this storage tree and are never modified by Stage Two.

## Bootstrap

Create the storage tree with:

```powershell
python manage.py stage-two bootstrap-storage
```

The implementation is `scripts/stage_two/storage/bootstrap.py`. It is idempotent and creates missing directories only.

## Main Storage Areas

| Area | Relative path | Purpose |
| --- | --- | --- |
| PostgreSQL runtime | `postgres/`, `pgadmin/` | Local database service state when using docker-compose. |
| Normalized Parquet | `parquet/normalized/` | Parser outputs. |
| Feature Parquet | `parquet/features/` | Feature artifact contract target. |
| Model-ready artifacts | `parquet/model_ready/` | Model-ready artifact contract target. |
| DuckDB | `duckdb/`, `duckdb/sql`, `duckdb/exports` | Local analytical views/check exports. |
| Reports | `reports/en/stage-two/`, `reports/ru/stage-two/` | Parser, normalization, quality, leakage, readiness reports. |
| Logs | `logs/stage-two/` | Stage Two operational logs. |
| Temp data | `temp_data/ingestion`, `temp_data/parser_runs`, `temp_data/normalization`, `temp_data/duckdb` | Intermediate diagnostics. |
| Config | `config/` | Runtime config files such as label mapping rules. |
| Schema copies | `schemas/normalized`, `schemas/features`, `schemas/model_ready` | Storage-side schema artifacts. |

## Normalized Parquet Layout

`ParquetArtifactWriter.write_normalized()` writes under:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Examples:

```text
parquet/normalized/dns/TRAIN/dns/example-dataset/schema=v1/part-42.parquet
parquet/normalized/host/VALIDATION/network_flow/example-dataset/schema=v1/part-43.parquet
parquet/normalized/host/TEST/sandbox/example-dataset/schema=v1/part-44.parquet
```

The Parquet path is registered in PostgreSQL `normalized_artifacts.normalized_path`.

## Report Layout

Coverage reports:

```text
reports/en/stage-two/parser/parser_coverage_matrix.md
reports/ru/stage-two/parser/parser_coverage_matrix.md
```

Parser run reports:

```text
reports/en/stage-two/parser/
reports/ru/stage-two/parser/
```

Normalization reports:

```text
reports/en/stage-two/normalization/
reports/ru/stage-two/normalization/
```

Quality and leakage reports:

```text
reports/en/stage-two/quality/
reports/en/stage-two/leakage/
reports/ru/stage-two/leakage/
```

## Storage Rules

- Store raw input only in the original raw dataset roots.
- Store large normalized rows in Parquet, not PostgreSQL.
- Store only metadata, counters, hashes, paths, and bounded diagnostics in PostgreSQL.
- Keep TRAIN, VALIDATION, TEST, and EXPERIMENTS separated in artifact paths.
- Use configured paths from `config.py`; do not hardcode absolute storage paths in parser code.
