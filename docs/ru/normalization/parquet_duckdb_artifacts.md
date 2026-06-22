# Parquet и DuckDB артефакты

Stage Two хранит большие таблицы в Parquet и использует DuckDB для аналитических SQL-проверок поверх этих файлов. PostgreSQL Catalog хранит только metadata: paths, row counts, hashes, schema versions, statuses и связи.

## Parquet writer

Код:

```text
scripts/stage_two/parquet/writer.py
```

`ParquetArtifactWriter`:

- пишет rows в Parquet;
- сериализует поля с суффиксом `_json` в deterministic JSON strings;
- по умолчанию использует compression `zstd`;
- считает `row_count`, `file_size_bytes`, optional `content_hash_sha256`;
- регистрирует artifacts через `ArtifactRepository`.

Hash output контролируется normalization option `--hash-output-artifacts`. Если hashing выключен, `content_hash_sha256` может быть пустой строкой.

## Пути normalized artifacts

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Пример:

```text
parquet/normalized/dns/TRAIN/dns_query/dns-train/schema=v1/part-42.parquet
```

Пишут:

- `DnsNormalizationService`;
- `HostNormalizationService`;
- `NormalizeFormatRunner`;
- legacy `normalize-dns`/`normalize-host`.

Catalog entry: `normalized_artifacts.normalized_path`.

## Пути feature artifacts

```text
parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Feature groups из contract:

```text
dns_features
host_syscall_features
host_eventlog_features
host_metrics_features
network_flow_features
hybrid_features
sequence_features
```

Catalog entry: `feature_artifacts.feature_path`.

В текущем CLI нет отдельной команды сборки feature artifacts. Реализованы contract helpers и writer service: `scripts/stage_two/features/contracts.py`, `scripts/stage_two/features/writer.py`.

## Пути model-ready artifacts

```text
parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}
```

Поддерживаемые `data_type`:

```text
X
y
sequence
split_index
preprocessing_metadata
```

Catalog entry: `model_ready_artifacts.artifact_path`.

`ModelReadyRegistryService` проверяет:

- `data_type` входит в contract;
- `X` rows не содержат forbidden leakage columns;
- preprocessing artifacts fitted only on `TRAIN`.

## DuckDB service

Код:

```text
scripts/stage_two/duckdb/service.py
```

DuckDB создает views поверх Parquet:

| View | Path pattern | Required columns |
| --- | --- | --- |
| `normalized_all` | `parquet/normalized/**/*.parquet` | `event_uid`, `dataset_role`, `branch`, `source_file_path` |
| `features_all` | `parquet/features/**/*.parquet` | `role`, `branch`, `feature_group` |
| `model_ready_all` | `parquet/model_ready/**/*.parquet` | `filename` |

Если matching Parquet файлов нет, service создает placeholder view с required columns, чтобы checks возвращали контролируемый результат, а не падали из-за отсутствия view.

## DuckDB checks

Команда:

```bash
python manage.py stage-two run-duckdb-checks
```

Проверки:

- row counts по views;
- наличие required columns;
- split contamination (`TRAIN`, `VALIDATION`, `TEST` не должны смешиваться);
- schema mismatch diagnostics.

Report сохраняется как:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

Через `register_report()` результат регистрируется в `data_quality_reports`.

## Ограничения

- DuckDB читает уже записанные Parquet files; он не заменяет PostgreSQL Catalog.
- Feature/model-ready paths могут существовать только после вызова соответствующих writer/registry services; CLI build step для них сейчас не реализован.
- Перемещение Parquet files без обновления catalog ломает traceability.
- `TRAIN`, `VALIDATION`, `TEST` должны оставаться раздельными на уровне path, catalog metadata и downstream artifacts.
