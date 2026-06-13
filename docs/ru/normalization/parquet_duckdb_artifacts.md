# Parquet и DuckDB artifacts

Parquet writer реализован в `scripts/stage_two/parquet/writer.py`. По умолчанию используется Zstandard compression (`zstd`). После записи вычисляются row count, file size и SHA-256 content hash.

## Artifact layers

Normalized:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Features:

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Model-ready:

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

## Feature artifact contract

Контракт находится в `schemas/features/feature_artifact_v1.json`. Реализованные feature groups:

- `dns_features`
- `host_syscall_features`
- `host_eventlog_features`
- `host_metrics_features`
- `network_flow_features`
- `hybrid_features`
- `sequence_features`

Feature writer исключает leakage/source/label columns из подсчета `feature_count`.

## Model-ready contract

Контракт находится в `schemas/model_ready/model_ready_v1.json`. Поддерживаются `X`, `y`, `sequence`, `split_index`, `preprocessing_metadata`.

Для `X` запрещены label/source/traceability columns. Валидация выполняется перед записью model-ready table artifacts.

## DuckDB analytics

DuckDB layer реализован в `scripts/stage_two/duckdb/service.py`. Команда:

```powershell
python manage.py stage-two run-duckdb-checks
```

Создаются views:

- `normalized_all`
- `features_all`
- `model_ready_all`

Views читают Parquet через `read_parquet(..., union_by_name=true, filename=true)`. Если файлов нет, создается пустой view с совместимыми колонками, чтобы проверки не падали на пустом storage.

Проверки включают row counts, required columns, split contamination и schema mismatch. Результат сохраняется в reports и регистрируется в `data_quality_reports`.
