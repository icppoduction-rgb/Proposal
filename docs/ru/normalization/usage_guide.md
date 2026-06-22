# Руководство запуска Stage Two normalization

Документ фиксирует фактический CLI слой: `manage.py` принимает `module`, `service`, `action`, `extra_args`, передает `stage-two` в `scripts.stage_two.cli.router_stage_two()`, а роутер вызывает конкретные service functions.

## Предварительные условия

Нужно настроить окружение:

```bash
export PATH_DATA_STORAGE=/absolute/path/to/stage-two-storage
export PATH_FOLDER_DATASETS_FILTER=/absolute/path/to/stage-one-filtered-or-sorted-tree
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/database
```

`DATABASE_URL` читается через `scripts/db/config.py`. Если переменной нет в окружении, код пробует загрузить `.env` из корня проекта.

## Базовый порядок запуска

```bash
python manage.py stage-two bootstrap-storage
alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 100
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Порядок сохраняет разделение ролей. Нормализация `TRAIN`, `VALIDATION` и `TEST` запускается отдельными командами или через `normalize-all`, который группирует файлы по `branch/role/source_format` и не объединяет роли в один output artifact.

## Команды Stage Two

| Команда | Назначение | Основной выход |
| --- | --- | --- |
| `bootstrap-storage` | Создает обязательные директории в `PATH_DATA_STORAGE`. | Storage tree, schema/report/temp/log directories. |
| `catalog-ingest` | Сканирует `PATH_FOLDER_DATASETS_FILTER`, регистрирует datasets/files. | `datasets`, `ingestion_runs`, `dataset_files`. |
| `seed-parser-registry` | Загружает `parser_registry_seed.json` в catalog. | `parser_registry`, `schema_versions`. |
| `parser-coverage [branch]` | Проверяет, есть ли parser для зарегистрированных `branch/role/source_format`. | Console report, parser coverage diagnostics. |
| `mark-ready` | Переводит файлы подходящего bucket в `READY_FOR_PARSING`. | Обновленные `dataset_files.status`. |
| `normalize-format` | Нормализует конкретный `branch/role/source_format`. | `parser_runs`, normalized Parquet, `normalized_artifacts`. |
| `normalize-all` | Нормализует все ready buckets по branch. | То же, по группам role/format. |
| `split-large-files` | Делит большие line-based files на chunks. | Chunk files, optional catalog registration. |
| `normalize-dns [limit]` | Legacy shortcut для DNS ready files. | Normalized DNS artifacts. |
| `normalize-host [limit]` | Legacy shortcut для Host ready files. | Normalized Host artifacts. |
| `run-duckdb-checks` | Создает DuckDB views поверх Parquet и запускает analytics checks. | DuckDB report, `data_quality_reports`. |
| `run-leakage-checks` | Проверяет model-ready/feature contracts на leakage. | Leakage reports, `data_quality_reports`. |
| `trace-artifact` | Восстанавливает lineage для model-ready artifact. | Console JSON trace chain. |

## `mark-ready`

Флаги:

```bash
python manage.py stage-two mark-ready \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --dry-run

python manage.py stage-two mark-ready \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --apply
```

Также поддерживается compact form:

```bash
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
```

Ограничения:

- `--dry-run` и `--apply` взаимоисключающие.
- `role` должен быть одним из `TRAIN`, `VALIDATION`, `TEST`.
- Команда работает только с metadata catalog, raw files не изменяет.

## `normalize-format`

Флаги:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --limit 100 \
  --workers 2 \
  --batch-size 50000 \
  --max-output-part-rows 50000 \
  --packet-mode packet-summary \
  --resume \
  --hash-output-artifacts
```

Компактная форма:

```bash
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
```

Поведение:

- выбирает `dataset_files` со статусом `READY_FOR_PARSING` для точного `branch/role/source_format`;
- через `ParserResolver` выбирает активный parser из `parser_registry`;
- если parser не найден, выбранные файлы помечаются `UNSUPPORTED_FORMAT`;
- пишет normalized Parquet и регистрирует `parser_runs`/`normalized_artifacts`;
- при `--workers > 1` использует `ProcessPoolExecutor`;
- при `--resume` пропускает файлы, для которых уже есть успешный normalized artifact.

`--packet-mode` поддерживает значения:

| Значение | Назначение |
| --- | --- |
| `packet-summary` | Безопасный режим для packet captures: summary-level parsing. |
| `dns-only` | Извлекать DNS-события из packet captures, где parser это поддерживает. |
| `sample` | Обрабатывать sample пакетов; требует `--sample-size`. |

## `normalize-all`

```bash
python manage.py stage-two normalize-all \
  --branch dns \
  --limit 1000 \
  --workers 2 \
  --resume
```

Компактная форма:

```bash
python manage.py stage-two normalize-all dns:1000
```

Команда выбирает ready groups внутри одной branch и запускает `NormalizeFormatRunner` по группам. Группировка выполняется по `role` и `source_format`; это защищает от смешивания `TRAIN`, `VALIDATION`, `TEST`.

## Legacy-команды

```bash
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

Эти команды оставлены для совместимости. Для воспроизводимых запусков предпочтительны `normalize-format` или `normalize-all`, потому что они явно задают branch/role/format и performance options.

## Разделение больших файлов

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TRAIN \
  --format csv \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Назначение: подготовить line-based files к нормализации, когда один файл слишком большой. Команда поддерживает `csv`, `pcap.csv`, `txt`, `json`, `json-1`, логовые форматы, `sc`, `ghc`, `netflow_day`, `netflow_ids`, `wls_day` и metricbeat-like logs. Binary formats (`cap`, `pcap`, `pcapng`, `bson`) не делятся этим splitter.

Важные правила:

- `--register` допустим только вместе с `--apply`;
- без `--apply` команда работает как dry run;
- chunks пишутся в `PATH_FOLDER_DATASETS_FILTER/chunked/...`;
- при регистрации chunks получают статус `READY_FOR_PARSING`;
- исходный файл может быть помечен `SKIPPED`, если не указан `--keep-source-ready`.

## Проверки

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

`run-duckdb-checks` строит views `normalized_all`, `features_all`, `model_ready_all` поверх Parquet и проверяет row counts, required columns, split contamination и schema mismatch. `run-leakage-checks` проверяет запретные X columns, отсутствие `TEST` в training/preprocessing fit и регистрирует CRITICAL нарушения.

## Trace artifact

```bash
python manage.py stage-two trace-artifact 123
python manage.py stage-two trace-artifact parquet/model_ready/tabular/dns/TRAIN/schema=v1/X_train.parquet
```

Числовой аргумент трактуется как `model_ready_artifacts.id`, строковый путь - как `model_ready_artifacts.artifact_path`. Команда требует, чтобы у model-ready artifact был `feature_artifact_id`, а у feature artifact - `normalized_artifact_id`; иначе traceability chain считается разорванной.

## Модульные проверки

Эти проверки не зарегистрированы как `manage.py stage-two` commands, но реализованы как Python modules:

```bash
python -m scripts.db.smoke_check
python -m scripts.stage_two.readiness_check
python -m scripts.stage_two.e2e_dry_run
```

`readiness_check` проверяет миграции, storage paths, counts catalog tables, parser coverage, normalized/feature/model-ready registration, quality/leakage reports, traceability и raw file hashes. `e2e_dry_run` создает synthetic DNS/Host samples под `temp_data`, прогоняет ingestion, seed, normalization, feature/model-ready registry services, DuckDB/leakage checks и traceability.

## Типовые ошибки

| Симптом | Причина | Действие |
| --- | --- | --- |
| `DATABASE_URL must be configured` | Нет `DATABASE_URL` в окружении или `.env`. | Настроить `DATABASE_URL`. |
| `PATH_DATA_STORAGE must be configured` | Storage root не задан. | Задать `PATH_DATA_STORAGE`, затем `bootstrap-storage`. |
| `No parser available` / `UNSUPPORTED_FORMAT` | В `parser_registry` нет активного parser для `branch/role/source_format`. | Проверить `parser-coverage`, добавить parser или registry entry. |
| Empty DuckDB views | Parquet layer пустой или paths не созданы. | Проверить `normalized_artifacts` и storage paths. |
| Leakage CRITICAL | X artifact содержит label/source fields или TEST участвует в fit/training. | Пересобрать artifact с корректным contract. |
