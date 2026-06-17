# Pipeline, artifacts и data contracts

## Stage One artifacts

Stage One outputs являются файловыми JSON/Markdown diagnostics:

| Этап | Команда | Основные outputs |
| --- | --- | --- |
| DNS discovery | `python manage.py handlers analyze-dataset dns-dataset-handler` | `dns-path-file.json`, `dns-file.json`. |
| Host discovery | `python manage.py handlers analyze-dataset host-dataset-handler` | `host-path-file.json`, `host-file.json`. |
| Host filter | `python manage.py handlers filter-dataset filter-host-dataset-handler` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`. |
| Sort | `python manage.py handlers sort sort-*-dataset-handler` | Sorted tree, `sort-*-format-summary.json`. |
| Save sort | `python manage.py handlers save-sort save-sort-*-dataset-handler` | `sort-path-dns-file.json`, `sort-path-host-file.json`. |
| Content analysis | `python manage.py handlers dns-analyze ...` / `host-analyze ...` | `analysis-*-summary.json`, Markdown reports. |

Stage One JSON не является стабильной normalized schema. Он нужен для диагностики и подготовки, но Stage Two production source of truth - PostgreSQL Catalog.

## Stage Two commands и outputs

| Шаг | Команда | Вход | Выход |
| --- | --- | --- | --- |
| 1 | `python manage.py stage-two bootstrap-storage` | `config.py` storage paths | Directories under `PATH_DATA_STORAGE`. |
| 2 | `python -m alembic -c scripts/db/migrations/alembic.ini upgrade head` | Alembic migrations | PostgreSQL Catalog schema. |
| 3 | `python manage.py stage-two seed-parser-registry` | `schemas/*.schema.json`, registry seed | `schema_versions`, `parser_registry`. |
| 4 | `python manage.py stage-two catalog-ingest` | Raw/sorted dataset roots | `ingestion_runs`, `datasets`, `dataset_files`. |
| 5 | `python manage.py stage-two parser-coverage` | Catalog + registry | RU/EN coverage matrix JSON/MD. |
| 6 | `python manage.py stage-two mark-ready ...` | `dataset_files` rows | Selected statuses changed to `READY_FOR_PARSING`. |
| 7 | `python manage.py stage-two normalize-format ...` | READY files for one branch/role/source_format | Parquet, `parser_runs`, `normalized_artifacts`, reports. |
| 8 | `python manage.py stage-two normalize-all ...` | READY files for branch | Same as above, grouped by role/source_format. |
| 9 | `python manage.py stage-two run-duckdb-checks` | Parquet + catalog metadata | Quality reports. |
| 10 | `python manage.py stage-two run-leakage-checks` | Catalog/artifact metadata | Leakage reports. |
| 11 | `python -m scripts.stage_two.readiness_check` | DB/storage/registry/reports | Readiness status. |

## Normalized event contract

Normalized events follow `schemas/normalized_event.schema.json`. Parser implementations build events with shared helpers and preserve traceability fields:

| Field group | Examples |
| --- | --- |
| Traceability | `dataset_id`, `file_id`, `dataset_name`, `dataset_role`, `branch`, `source_format`, `source_file_path`, `source_file_hash`. |
| Parser metadata | `parser_name`, `parser_version`, `parser_run_id`, `schema_name`, `schema_version`. |
| Event identity | `event_uid`, `event_index`, `timestamp`, `timestamp_type`. |
| Canonical fields | `domain`, `query_domain`, `src_ip`, `dst_ip`, `process_name`, `user_name`, `host_name`, `event_type`, `modality`. |
| Labels | `label_binary`, `label_source`, `label_status`. |
| Preservation | `raw_fields_json`, `metadata_json`, `features_json` where applicable. |

Missing values должны оставаться `NULL`/`None`, а не подменяться искусственными defaults. Unknown fields сохраняются в `raw_fields_json`/`metadata_json`, если это безопасно и не содержит огромный payload.

## Parser result contract

Parser returns:

```text
ParseResult
  events: list[ParsedEvent]
  status
  counters
  warnings
  errors/error samples
  metadata
```

Required counters:

```text
rows_read
rows_parsed
rows_failed
bytes_read
files_read
warnings_count
parse_errors_count
```

Parser не должен менять raw file и не должен хранить full binary payload в PostgreSQL/report metadata.

## Parquet layout

Normalized artifacts пишутся под storage root:

```text
PATH_DATA_STORAGE/
  parquet/
    normalized/
      {branch}/
        {role}/
          {modality}/
            {dataset_slug}/
              schema={schema_version}/
                part-{parser_run_id}.parquet
```

Catalog row `normalized_artifacts` содержит path, relative path, hash, row count, schema metadata и `parser_run_id`. Payload читается через Parquet/DuckDB.

## Reports layout

```text
PATH_DATA_STORAGE/reports/en/stage-two/parser/
PATH_DATA_STORAGE/reports/ru/stage-two/parser/
PATH_DATA_STORAGE/reports/en/stage-two/normalization/
PATH_DATA_STORAGE/reports/ru/stage-two/normalization/
```

Coverage files:

```text
parser_coverage_matrix.json
parser_coverage_matrix.md
```

Reports должны быть диагностическими: counters/status/warnings/errors samples/hints, но не full raw payload.

## Traceability chain

Фактическая цепочка:

```text
dataset_files
  -> parser_runs
  -> normalized_artifacts
  -> feature_artifacts
  -> model_ready_artifacts
```

На текущем parser pipeline стабильно создаются `parser_runs` и `normalized_artifacts`. Feature/model-ready tables и writers существуют для следующих стадий, но общий production CLI для полного feature/model-ready workflow не реализован.

## Validation commands

```powershell
python -m compileall manage.py config.py scripts
git diff --check
python -m scripts.db.smoke_check
python -m alembic -c scripts/db/migrations/alembic.ini current
python manage.py stage-two parser-coverage
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Не заявляйте full-corpus success, если эти команды не запускались на полном corpus и доступной PostgreSQL DB.
