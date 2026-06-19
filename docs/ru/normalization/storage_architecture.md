# Storage architecture

Stage Two использует `PATH_DATA_STORAGE` как root для generated data и reports. Значение берется из environment через `config.py`.

Raw datasets находятся вне этого storage tree и никогда не изменяются Stage Two.
Текущий рабочий вход Stage Two - `PATH_FOLDER_DATASETS_FILTER`, а не `PATH_FOLDER_DATASETS`. Raw root сохраняется для immutable source storage, Stage One discovery и аудита/traceback.

## Bootstrap

```powershell
python manage.py stage-two bootstrap-storage
```

Implementation: `scripts/stage_two/storage/bootstrap.py`. Команда idempotent и создает только missing directories.

## Основные storage areas

| Area | Relative path | Purpose |
| --- | --- | --- |
| PostgreSQL runtime | `postgres/`, `pgadmin/` | Local database service state при использовании docker-compose. |
| Normalized Parquet | `parquet/normalized/` | Parser outputs. |
| Feature Parquet | `parquet/features/` | Target для feature artifact contract. |
| Model-ready artifacts | `parquet/model_ready/` | Target для model-ready artifact contract. |
| DuckDB | `duckdb/`, `duckdb/sql`, `duckdb/exports` | Analytical views/check exports. |
| Reports | `reports/en/stage-two/`, `reports/ru/stage-two/` | Parser, normalization, quality, leakage, readiness reports. |
| Logs | `logs/stage-two/` | Stage Two operational logs. |
| Temp data | `temp_data/ingestion`, `temp_data/parser_runs`, `temp_data/normalization`, `temp_data/duckdb` | Intermediate diagnostics. |
| Config | `config/` | Runtime config files, например label mapping rules. |
| Schema copies | `schemas/normalized`, `schemas/features`, `schemas/model_ready` | Storage-side schema artifacts. |

## Normalized Parquet layout

`ParquetArtifactWriter.write_normalized()` пишет:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Examples:

```text
parquet/normalized/dns/TRAIN/dns/example-dataset/schema=v1/part-42.parquet
parquet/normalized/host/VALIDATION/network_flow/example-dataset/schema=v1/part-43.parquet
parquet/normalized/host/TEST/sandbox/example-dataset/schema=v1/part-44.parquet
```

Parquet path регистрируется в PostgreSQL `normalized_artifacts.normalized_path`.

## Report layout

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

Quality/leakage reports:

```text
reports/en/stage-two/quality/
reports/en/stage-two/leakage/
reports/ru/stage-two/leakage/
```

## Storage rules

- Raw input хранится только в original raw dataset roots.
- `PATH_FOLDER_DATASETS_FILTER` используется как источник Stage Two catalog и normalization.
- Большие normalized rows хранятся в Parquet, не PostgreSQL.
- PostgreSQL хранит metadata, counters, hashes, paths и bounded diagnostics.
- TRAIN, VALIDATION и TEST разделены в catalog rows и artifact paths.
- `EXPERIMENTS` не создается и не обрабатывается в Stage Two.
- Parser code должен брать paths из `config.py`, а не hardcode absolute paths.
