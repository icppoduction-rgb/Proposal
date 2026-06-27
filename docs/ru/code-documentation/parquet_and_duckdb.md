# Parquet и DuckDB артефакты

## Почему Parquet

Parquet используется для больших сгенерированных таблиц:

- normalized events;
- feature artifacts;
- model-ready artifacts.

PostgreSQL catalog хранит metadata и paths, а не табличные данные строк. Это сохраняет catalog компактным и позволяет DuckDB делать SQL-проверки поверх columnar data.

## Запись Parquet

Файл: `scripts/stage_two/parquet/writer.py`.

Класс: `ParquetArtifactWriter`.

Compression по умолчанию:

```text
zstd
```

`_write_rows()`:

1. нормализует JSON suffix columns (`*_json`) в детерминированные JSON strings;
2. строит PyArrow table;
3. записывает Parquet;
4. возвращает `ParquetWriteResult`.

`ParquetWriteResult`:

| Поле | Значение |
|---|---|
| `absolute_path` | полный filesystem path |
| `relative_path` | path относительно `PATH_DATA_STORAGE` |
| `row_count` | количество записанных строк |
| `file_size_bytes` | размер Parquet file |
| `content_hash_sha256` | optional output hash, пустой если hash не включен |

## Пути артефактов

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

## Регистрация в catalog

| Метод writer | Таблица catalog |
|---|---|
| `register_normalized_artifact()` | `normalized_artifacts` |
| `register_feature_artifact()` | `feature_artifacts` |
| `register_model_ready_artifact()` | `model_ready_artifacts` |

В catalog сохраняются relative paths:

- `normalized_artifacts.normalized_path`;
- `feature_artifacts.feature_path`;
- `model_ready_artifacts.artifact_path`.

## Сервис DuckDB

Файл: `scripts/stage_two/duckdb/service.py`.

Класс: `DuckDBAnalyticsService`.

База данных по умолчанию:

```text
PATH_DATA_STORAGE/duckdb/proposal_analytics.duckdb
```

Представления:

| Представление | Pattern |
|---|---|
| `normalized_all` | `parquet/normalized/**/*.parquet` |
| `features_all` | `parquet/features/**/*.parquet` |
| `model_ready_all` | `parquet/model_ready/**/*.parquet` |

Представления создаются через:

```sql
read_parquet('<glob>', union_by_name = true, filename = true)
```

Если файлы не найдены, service создает empty view со стабильными placeholder columns.

## Проверки DuckDB

`run_checks()` выполняет:

- проверки row count с группировкой по доступным role/branch columns или filename path;
- проверки отсутствующих обязательных columns;
- проверку split contamination;
- проверку schema mismatch.

Обязательные columns:

| View | Обязательные columns |
|---|---|
| `normalized_all` | `event_uid`, `dataset_role`, `branch`, `source_file_path` |
| `features_all` | `role`, `branch`, `feature_group` |
| `model_ready_all` | `filename` |

Путь отчета:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

`register_report()` пишет aggregate row в `data_quality_reports`.

## SQL-шаблон

`scripts/stage_two/duckdb/sql/create_views.sql` содержит прямой SQL template с placeholder `${PATH_DATA_STORAGE}`. Python service безопаснее для runtime, потому что обрабатывает empty views и escaping путей.
