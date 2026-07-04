# Команды Stage Two normalization

Документ описывает реализованные команды Stage Two normalization и операционный порядок запуска. Источники проверки: `manage.py`, `scripts/router_script.py`, `scripts/stage_two/cli.py`, сервисы `scripts/stage_two/*` и файл `stage_two_dns_host_normalization_commands.txt`.

Главная точка входа:

```bash
python manage.py stage-two <command> [args]
```

`manage.py` принимает `module`, `service`, `action`, `extra_args`; `scripts/router_script.py` направляет `module=stage-two` в `scripts.stage_two.cli.router_stage_two()`. Неизвестная Stage Two команда возвращает ошибку `unknown Stage Two command`.

Сверка с кодом от 2026-07-04: fallback-текст из `config.manage_commands` не является полным help по Stage Two. В нем нет части новых router-команд, включая `parser-coverage`, `mark-ready`, `normalize-format`, `normalize-all`, `benchmark-normalization` и `split-large-files`. Источник истины по реализованным Stage Two командам - `scripts/stage_two/cli.py`.

## Полный порядок запуска

```bash
python manage.py stage-two bootstrap-storage
alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage

# Операционный шаг: выбрать bucket и подготовить только нужный branch/role/format.
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply

# Опциональный benchmark перед полным запуском.
python manage.py stage-two benchmark-normalization --branch dns --role TRAIN --format csv --limit 1000 --sample-ratio 0.10 --dry-run

# Основной точный запуск для production/runbook.
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 100 --workers 1 --resume

# Legacy shortcuts, если нужен запуск всех ready DNS или Host файлов.
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10

python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

`TRAIN`, `VALIDATION` и `TEST` запускаются отдельными bucket-командами или через `normalize-all`, который группирует работу по `role/source_format`. `TEST` не используется для обучения, fit preprocessing, scaler/encoder fit, feature selection или threshold tuning.

## Команды и операционные шаги

| Шаг | Команда | Реализовано в CLI | Назначение |
| --- | --- | --- | --- |
| 1 | `bootstrap-storage` | Да | Создать обязательное дерево `PATH_DATA_STORAGE`. |
| 2 | `catalog-ingest` | Да | Зарегистрировать Stage One filtered/sorted files в PostgreSQL Catalog. |
| 3 | `seed-parser-registry` | Да | Загрузить schema/parser metadata из seed-файла. |
| 4 | `parser-coverage [branch]` | Да | Проверить покрытие parser registry для catalog buckets. |
| 5 | `mark-ready` | Да | Перевести выбранные файлы в `READY_FOR_PARSING`. |
| 6 | `split-large-files` | Да | Разбить большие line-based ready files на chunks. |
| 7 | `normalize-format` | Да | Нормализовать один `branch/role/source_format`. |
| 8 | `normalize-all` | Да | Нормализовать все ready buckets внутри одной ветки `dns` или `host`. |
| 9 | `benchmark-normalization` | Да | Измерить скорость одного точного bucket `branch/role/source_format` и оценить throughput. |
| 10 | `normalize-dns [limit]` | Да | Legacy shortcut для DNS files со статусом `READY_FOR_PARSING`. |
| 11 | `normalize-host [limit]` | Да | Legacy shortcut для Host files со статусом `READY_FOR_PARSING`. |
| 12 | `run-duckdb-checks` | Да | Создать DuckDB views и записать analytics report. |
| 13 | `run-leakage-checks` | Да | Проверить model-ready/feature contracts на leakage. |
| 14 | `trace-artifact` | Да | Восстановить lineage для model-ready artifact. |
| - | `readiness_check`, `e2e_dry_run` | Нет как `manage.py stage-two` | Запускаются как Python modules. |

## `bootstrap-storage`

```bash
python manage.py stage-two bootstrap-storage
```

**Что делает:** идемпотентно создает обязательные директории Stage Two в `PATH_DATA_STORAGE`: `postgres/`, `pgadmin/`, `parquet/normalized/`, `parquet/features/`, `parquet/model_ready/`, `duckdb/sql/`, `duckdb/exports/`, `logs/stage-two/`, `backups/`, `temp_data/`, `schemas/`, `reports/ru/stage-two/`, `reports/en/stage-two/`, `config/`.

**Когда запускать:** один раз при подготовке окружения и повторно после изменения storage contract. Повторный запуск не удаляет существующие файлы.

**Входные данные:** переменная `PATH_DATA_STORAGE`.

**Артефакты:** директории под storage root. Parquet и отчеты на этом шаге не создаются.

**PostgreSQL:** не читает и не пишет таблицы.

**Возможные ошибки:** `PATH_DATA_STORAGE must be configured before bootstrapping storage`, отказ доступа к директории.

**Проверка успеха:** CLI выводит `root`, `created_count`, `existing_count`; директории существуют на диске.

## `catalog-ingest`

```bash
python manage.py stage-two catalog-ingest
```

**Что делает:** сканирует `PATH_FOLDER_DATASETS_FILTER`, определяет `branch`, `role`, `source_format`, считает размер, mtime и SHA-256, затем регистрирует datasets/files в PostgreSQL Catalog. Raw-файлы не изменяются.

**Когда запускать:** после Stage One sorted/filter tree и после появления новых или измененных файлов.

**Входные данные:** `PATH_FOLDER_DATASETS_FILTER`, доступная БД, примененные Alembic migrations.

**Артефакты:** внешних Parquet artifacts не создает.

**PostgreSQL:** пишет `ingestion_runs`, `datasets`, `dataset_files`. Новые поддержанные непустые файлы получают `REGISTERED`; пустые - `EMPTY_FILE`; неподдержанные scanner-форматы - `UNSUPPORTED_FORMAT`; измененные файлы учитываются в счетчике `files_changed`.

**Возможные ошибки:** отсутствует `PATH_FOLDER_DATASETS_FILTER`, нет подключения к БД, ошибка чтения файла, ошибка hash/stat.

**Проверка успеха:** CLI выводит `run_count` и список runs со статусом `SUCCESS` или `PARTIAL_SUCCESS`; в `dataset_files` появились строки по нужным `branch/role/source_format`.

## `seed-parser-registry`

```bash
python manage.py stage-two seed-parser-registry
```

**Что делает:** загружает schema metadata и parser registry entries из `scripts/stage_two/parser_registry/parser_registry_seed.json`.

**Когда запускать:** после миграций и перед `mark-ready`/normalization. Повторный запуск обновляет существующие registry entries.

**Входные данные:** seed JSON, доступные parser classes в `scripts/stage_two/parsers/*`, подключение к БД.

**Артефакты:** файловых artifacts не создает.

**PostgreSQL:** пишет/обновляет `schema_versions` и `parser_registry`.

**Возможные ошибки:** невалидный seed, отсутствующий parser module/class, ошибка БД.

**Проверка успеха:** CLI выводит `schema_version_id`, `inserted`, `updated`; `parser-coverage` показывает `parser_active=yes` для поддержанных buckets.

## `parser-coverage`

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage dns
python manage.py stage-two parser-coverage host
```

**Что делает:** строит матрицу `branch/role/source_format` по catalog counts и `parser_registry`, проверяет, найден ли активный parser и доступен ли parser class.

**Когда запускать:** после `catalog-ingest` и `seed-parser-registry`, а также перед массовым `mark-ready`.

**Входные данные:** `dataset_files`, `datasets`, `parser_registry`, Stage One path JSON только для diagnostics.

**Артефакты:** parser coverage reports через `scripts.stage_two.reports.parser_reports`.

**PostgreSQL:** читает `datasets`, `dataset_files`, `parser_registry`; статусы файлов не меняет.

**Возможные ошибки:** неизвестный branch, невалидный parser class, пустой catalog, расхождение catalog и registry.

**Проверка успеха:** итоговый payload имеет `status=SUCCESS`; строки с реальными файлами имеют `parser_active=yes`. Если `catalog_gap_rows` или `missing_parser_rows` больше нуля, сначала исправить registry/parser coverage.

## Операционный шаг `READY_FOR_PARSING`

Подготовка к `READY_FOR_PARSING` реализована командой `mark-ready`. Если команда не используется, тот же переход остается ручным catalog operation и должен выполняться только после проверки parser coverage.

```bash
python manage.py stage-two mark-ready --branch host --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format csv --apply
```

Компактная форма:

```bash
python manage.py stage-two mark-ready dry-run:host:TRAIN:csv
python manage.py stage-two mark-ready apply:host:TRAIN:csv
```

**Что делает:** выбирает файлы активного source group по точному `branch/role/source_format`, проверяет parser resolver и переводит eligible rows в `READY_FOR_PARSING`.

**Когда запускать:** после `parser-coverage`, отдельно для каждого нужного bucket. Сначала `--dry-run`, затем `--apply`.

**Входные данные:** `--branch`, `--role`, `--format`; parser registry entry для bucket.

**Артефакты:** JSON/Markdown reports в `reports/{ru,en}/stage-two/status/`, если настроен `PATH_DATA_STORAGE`.

**PostgreSQL:** читает `datasets`, `dataset_files`, `parser_registry`; меняет `dataset_files.status` на `READY_FOR_PARSING` только для eligible files. По умолчанию eligible statuses: `REGISTERED`, `CHANGED`, `DISCOVERED`. С `--retry-failed` eligible statuses: `FAILED`, `SKIPPED`, `PARTIALLY_PARSED`.

**Возможные ошибки:** отсутствует parser (`UNSUPPORTED_FORMAT`), неверный role, одновременные `--dry-run` и `--apply`, пустой `--format`, неподходящие текущие статусы (`PARSED`, `EMPTY_FILE`, `READY_FOR_PARSING` и т.д.).

**Проверка успеха:** `dry_run=false`, `status=SUCCESS`, `updated > 0`; report показывает переходы `<previous_status> -> READY_FOR_PARSING`.

## `split-large-files`

```bash
python manage.py stage-two split-large-files \
  --branch dns \
  --role TEST \
  --format csv \
  --limit 1 \
  --max-part-size-gb 2 \
  --min-size-gb 1 \
  --header no \
  --apply \
  --register
```

**Что делает:** делит большие line-based файлы со статусом `READY_FOR_PARSING` на chunks. Поддержанные форматы включают `csv`, `pcap.csv`, `txt`, `json`, `json-1`, log formats, `ghc`, `sc`, `netflow_day`, `netflow_ids`, `wls_day` и metricbeat-like logs. Binary formats (`cap`, `pcap`, `pcapng`, `bson`) этим splitter не делятся.

**Когда запускать:** перед `normalize-format`, если один файл слишком большой для доступной RAM/времени. Для DNS TEST csv из runbook используется `--header no`.

**Входные данные:** готовые catalog rows (`READY_FOR_PARSING`), исходный файл на диске, параметры размера part.

**Артефакты:** chunk files под `PATH_FOLDER_DATASETS_FILTER/chunked/...`.

**PostgreSQL:** при `--register` регистрирует chunks в `dataset_files` со статусом `READY_FOR_PARSING`; исходный файл может быть переведен в `SKIPPED`, если не указан `--keep-source-ready`.

**Возможные ошибки:** `--register` без `--apply`, unsupported binary format, исходный файл отсутствует, output dir уже существует без `--overwrite`, неверный `--header`.

**Проверка успеха:** CLI выводит `status=SUCCESS`, `chunks_created > 0`, `registered > 0`; `normalize-format` затем выбирает chunks, а не исходный большой файл.

## `normalize-format`

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format csv \
  --limit 100 \
  --workers 1 \
  --batch-size 10000 \
  --max-output-part-rows 50000 \
  --packet-mode packet-summary \
  --resume
```

Компактная форма:

```bash
python manage.py stage-two normalize-format host:TRAIN:csv:100
```

**Что делает:** выбирает `dataset_files.status=READY_FOR_PARSING` для одного `branch/role/source_format`, разрешает parser через registry, запускает DNS или Host normalization service, пишет normalized Parquet parts и регистрирует artifacts.

**Когда запускать:** основной рекомендуемый способ нормализации, особенно для runbook из `stage_two_dns_host_normalization_commands.txt`, потому что он явно фиксирует branch, role и format.

**Входные данные:** ready files, parser registry entry, normalized schema version, raw file path, storage root.

**Артефакты:** normalized Parquet:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Также создаются parser run reports в `reports/{ru,en}/stage-two/parser/`.

**PostgreSQL:** читает `dataset_files`, `datasets`, `parser_registry`, `schema_versions`; пишет `parser_runs`, `normalized_artifacts`; обновляет `dataset_files.status` на `PARSED`, `PARTIALLY_PARSED`, `FAILED` или `UNSUPPORTED_FORMAT`.

**Возможные ошибки:** нет parser, parser class не импортируется, файл отсутствует, ошибка парсинга, нехватка памяти, неверные числовые параметры, `packet_mode` не поддержан конкретным parser.

**Проверка успеха:** CLI выводит `status=SUCCESS`, `parsed + partially_parsed > 0`, `failed=0`, `unsupported=0`; Parquet files существуют; `normalized_artifacts` содержит paths; `parser_runs.status` не `FAILED`.

## `normalize-all`

```bash
python manage.py stage-two normalize-all \
  --branch host \
  --limit 1000 \
  --workers 2 \
  --batch-size 10000 \
  --max-output-part-rows 50000 \
  --resume
```

Компактная форма:

```bash
python manage.py stage-two normalize-all host:1000
```

**Что делает:** обходит ready groups внутри одной branch и вызывает `normalize-format` по каждой группе `role/source_format`.

**Когда запускать:** когда parser coverage проверен и нужно обработать несколько ready buckets внутри `dns` или `host`.

**Входные данные:** `--branch dns|host`, ready files.

**Артефакты:** те же, что у `normalize-format`, но по нескольким группам.

**PostgreSQL:** те же таблицы, что у `normalize-format`; роли не смешиваются, потому что каждая группа запускается отдельно.

**Возможные ошибки:** частичный failure одного bucket дает общий `PARTIAL_SUCCESS`; неподдержанный parser приводит к `UNSUPPORTED_FORMAT` для соответствующей группы.

**Проверка успеха:** `groups_count > 0`, `status=SUCCESS`; каждая group summary имеет `failed=0`, `unsupported=0`.

## `normalize-dns` и `normalize-host`

```bash
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

**Что делает:** legacy shortcut. Выбирает files со статусом `READY_FOR_PARSING` для `branch=dns` или `branch=host` и запускает соответствующий normalization service. Единственный позиционный аргумент - optional non-negative integer `limit`.

**Когда запускать:** для быстрой проверки или обратной совместимости. Для воспроизводимых batch-запусков предпочтительнее `normalize-format`, потому что там явно указан `role/source_format` и доступны performance options.

**Входные данные:** ready files выбранной ветки.

**Артефакты:** normalized Parquet и catalog records как у `normalize-format`.

**PostgreSQL:** пишет `parser_runs`, `normalized_artifacts`; обновляет `dataset_files.status`.

**Возможные ошибки:** больше одного аргумента, нечисловой limit, parser/file errors.

**Проверка успеха:** CLI выводит `files_seen`, `normalized`, `skipped`; для полного контроля дополнительно проверить `parser_runs` и `normalized_artifacts`.

## `run-duckdb-checks`

```bash
python manage.py stage-two run-duckdb-checks
```

**Что делает:** создает DuckDB views `normalized_all`, `features_all`, `model_ready_all` поверх Parquet и выполняет analytics checks: row counts, missing required columns, split contamination, schema mismatch.

**Когда запускать:** после нормализации и после появления feature/model-ready artifacts.

**Входные данные:** `PATH_DATA_STORAGE`, Parquet layers, DuckDB package.

**Артефакты:** JSON report `reports/en/stage-two/quality/duckdb_analytics_report.json`; DuckDB database path из storage config.

**PostgreSQL:** пишет aggregate report в `data_quality_reports` с `check_group=duckdb`, severity `INFO` или `ERROR`.

**Возможные ошибки:** `PATH_DATA_STORAGE` не задан, DuckDB не установлен, Parquet files отсутствуют или имеют несовместимые схемы.

**Проверка успеха:** CLI выводит `status=SUCCESS`, `check_count`, `catalog_report_id`; report не содержит failed checks.

## `run-leakage-checks`

```bash
python manage.py stage-two run-leakage-checks
```

**Что делает:** проверяет leakage rules поверх DuckDB views и catalog context. Критичные правила включают запрет label/source/trace fields в model-ready X artifacts и запрет `TEST` rows в training artifacts.

**Когда запускать:** после сборки feature/model-ready artifacts и перед использованием данных для обучения.

**Входные данные:** Parquet `features`/`model_ready`, DuckDB views, catalog metadata.

**Артефакты:** leakage reports в `reports/{ru,en}/stage-two/leakage/`.

**PostgreSQL:** пишет `data_quality_reports` с `check_group=leakage`; failed leakage checks получают severity `CRITICAL`.

**Возможные ошибки:** пустые model-ready views, forbidden X columns, `TEST` contamination, несогласованные роли в artifact paths/columns.

**Проверка успеха:** CLI выводит `status=SUCCESS`, severity не `CRITICAL`, `check_count`; report не содержит failed leakage checks.

## `trace-artifact`

```bash
python manage.py stage-two trace-artifact 123
python manage.py stage-two trace-artifact parquet/model_ready/tabular/dns/TRAIN/schema=v1/X_train.parquet
```

**Что делает:** восстанавливает цепочку lineage для model-ready artifact. Числовой аргумент трактуется как `model_ready_artifacts.id`, строковый - как `model_ready_artifacts.artifact_path`.

**Когда запускать:** после создания model-ready artifacts или при расследовании качества/утечки.

**Входные данные:** id или path model-ready artifact.

**Артефакты:** файлов не создает; печатает JSON trace chain в stdout.

**PostgreSQL:** читает цепочку:

```text
model_ready_artifacts.feature_artifact_id
  -> feature_artifacts.id
  -> feature_artifacts.normalized_artifact_id
  -> normalized_artifacts.id
  -> normalized_artifacts.parser_run_id
  -> parser_runs.id
  -> parser_runs.file_id
  -> dataset_files.id
  -> dataset_files.dataset_id
  -> datasets.id
```

**Возможные ошибки:** artifact не найден, отсутствует `feature_artifact_id`, отсутствует `normalized_artifact_id`, разорванная catalog chain.

**Проверка успеха:** команда печатает JSON с dataset, source file, parser run, normalized artifact, feature artifact и model-ready artifact.

## Команды из операционного runbook

`stage_two_dns_host_normalization_commands.txt` содержит практические batch-команды для оставшихся DNS/Host форматов. Они соответствуют реализованным CLI-командам:

- `mark-ready --dry-run/--apply` для каждого `branch/role/source_format`;
- `split-large-files` для больших line-based files;
- `normalize-format` с `--workers`, `--batch-size`, `--max-output-part-rows`, `--packet-mode`, `--sample-size`, `--resume`;
- `parser-coverage`, `run-duckdb-checks`, `run-leakage-checks` как проверки после запуска.

Файл содержит Windows-specific команды `cd` и `conda activate`; они являются инструкциями окружения, а не частью CLI проекта. Команда `python -m scripts.stage_two.readiness_check` реализована как module check, но не зарегистрирована в `router_stage_two`.

## Инварианты запуска

1. Raw-файлы не изменяются; Stage Two создает metadata и новые artifacts.
2. `TRAIN`, `VALIDATION`, `TEST` обрабатываются отдельными bucket-командами.
3. `TEST` не участвует в fit/training/tuning.
4. Labels не являются X features.
5. Отсутствующий label не означает benign.
6. Отсутствующий timestamp нельзя заменять текущим временем.
7. Все artifacts должны сохранять traceability `raw -> normalized -> features -> model-ready`.
## Performance commands и profiles

Текущий CLI также включает `benchmark-normalization` и resource profiles для `normalize-format` / `normalize-all`.

### `benchmark-normalization`

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Поддерживаемые options:

- `--branch`;
- `--role`;
- `--format`;
- `--limit`;
- `--sample-ratio`;
- `--resource-profile`;
- `--workers`;
- `--batch-size`;
- `--max-output-part-rows`;
- `--resume`;
- `--dry-run`.

Report содержит `input_bytes`, `processed_bytes`, `processed_gb`, `elapsed_seconds`, `gb_per_hour`, rates по files/rows/events, failed/partial/skipped/unsupported files, Parquet output size, average parser/write time, `estimated_time_for_17gb` и `meets_3_hour_target`.

Actual benchmark run включает safe resume behavior, если не указан `--dry-run`; повторный benchmark не должен создавать дубли successful normalized artifacts.

### Resource profiles

| Profile | workers | batch_size | max_output_part_rows | packet_batch_size |
| --- | ---: | ---: | ---: | ---: |
| `safe` | 4 | 50000 | 100000 | 50000 |
| `balanced` | 8 | 100000 | 250000 | 50000 |
| `fast` | 12 | 200000 | 500000 | 50000 |
| `aggressive` | 14 | 300000 | 750000 | 50000 |

CLI overrides имеют приоритет над profile и format policy. Пример:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --workers 6 \
  --resume
```

Итог: `workers=6`, остальные значения берутся из `fast`, если format policy не ограничит рискованный формат.

### Безопасные PCAP/BSON примеры

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume

python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

### Большие line-based files

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TEST \
  --format txt \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Не делите `cap`, `pcap`, `pcapng` или `bson` обычным line splitter.

### Обязательные gates после performance runs

`normalize-format` сохраняет post-run validation summary. После performance runs также запускайте:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Если `run-leakage-checks` возвращает CRITICAL, не используйте затронутые feature/model-ready artifacts.
