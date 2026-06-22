# Документация по коду проекта

Этот раздел описывает кодовую базу `Proposal`: инвентаризацию и анализ Stage One, pipeline нормализации Stage Two, каталог PostgreSQL, контракты схем, стратегию парсеров, обработку меток, Parquet/DuckDB-артефакты, проверки качества/утечек и точки расширения.

Документация нужна разработчику, который подключается к проекту без предварительного чтения всего кода. Она фиксирует не только назначение файлов, но и контракты данных, порядок запуска, статусы, ограничения и зоны риска.

## Карта документов

| Документ | Назначение |
|---|---|
| [cli_and_routing.md](cli_and_routing.md) | `manage.py`, слой маршрутизации, команды Stage One/Stage Two, порядок запуска |
| [stage_one_handlers.md](stage_one_handlers.md) | handlers Stage One: анализ, фильтрация, сортировка, экспорт путей, анализ содержимого, JSON |
| [stage_two_overview.md](stage_two_overview.md) | pipeline Stage Two: storage, ingestion, registry, normalization, checks |
| [storage_architecture.md](storage_architecture.md) | `PATH_DATA_STORAGE`, обязательные директории, пути артефактов |
| [postgresql_catalog.md](postgresql_catalog.md) | таблицы PostgreSQL catalog и цепочка трассируемости |
| [sqlalchemy_layer.md](sqlalchemy_layer.md) | config/session/models/repositories/migrations/smoke check |
| [normalized_event_schema.md](normalized_event_schema.md) | `normalized_event_v1`, поля, timestamp, labels, traceability |
| [parser_strategy.md](parser_strategy.md) | parser registry, resolver, parser classes, статусы parser runs |
| [label_resolver.md](label_resolver.md) | источники labels, ограничения TEST, конфликтные labels |
| [parquet_and_duckdb.md](parquet_and_duckdb.md) | Parquet writer, пути, compression, DuckDB views/checks |
| [data_quality_checks.md](data_quality_checks.md) | DataQualityChecker, DuckDB analytics, отчеты |
| [data_leakage_prevention.md](data_leakage_prevention.md) | запрещенные X-колонки, инварианты TRAIN/VALIDATION/TEST |
| [traceability.md](traceability.md) | цепочка raw -> normalized -> features -> model-ready |
| [dataset_contracts.md](dataset_contracts.md) | DNS/Host TRAIN/VALIDATION/TEST форматы, количества, labels, потребности parser |
| [extension_points.md](extension_points.md) | как добавлять handlers, parsers, schemas, labels, checks, stages |
| [risks_and_technical_debt.md](risks_and_technical_debt.md) | известные ограничения, parser gaps, риски leakage/timestamp/large files |

## Рекомендуемый порядок чтения

1. [cli_and_routing.md](cli_and_routing.md)
2. [stage_one_handlers.md](stage_one_handlers.md)
3. [stage_two_overview.md](stage_two_overview.md)
4. [postgresql_catalog.md](postgresql_catalog.md)
5. [normalized_event_schema.md](normalized_event_schema.md)
6. [parser_strategy.md](parser_strategy.md)
7. [label_resolver.md](label_resolver.md)
8. [data_leakage_prevention.md](data_leakage_prevention.md)
9. [dataset_contracts.md](dataset_contracts.md)
10. [risks_and_technical_debt.md](risks_and_technical_debt.md)

## Stage One

Stage One анализирует файловую структуру DNS/Host датасетов, создает JSON-инвентари, фильтрует Host-источники, сортирует файлы по ролям и форматам, экспортирует карты путей sorted tree и генерирует отчеты анализа содержимого.

Фактические компоненты находятся в `scripts/handlers`:

```text
scripts/handlers/
  analyze_dataset/
  filter_dataset/
  sort/
  save_sort/
  dns_analyze/
  host_analyze/
  json_handler/
```

Stage One не регистрирует файлы в PostgreSQL и не пишет normalized/features/model-ready артефакты. Его результаты используются как filesystem/JSON-основа для дальнейшего catalog ingestion и стратегии парсеров.

## Stage Two

Stage Two создает storage-структуру, регистрирует raw-файлы в PostgreSQL catalog, seed-ит metadata схем и парсеров, выбирает parser, нормализует события в Parquet, пишет parser reports, выполняет DuckDB checks, quality/leakage checks и обеспечивает трассируемость raw -> normalized -> features -> model-ready.

Фактические компоненты находятся в `scripts/stage_two`, `scripts/db`, `schemas`.

## Ключевые инварианты

1. Raw-файлы датасетов не изменяются.
2. `TRAIN`, `VALIDATION` и `TEST` не смешиваются в одном model-ready artifact.
3. `TEST` не используется для обучения, fit preprocessing, fit scaler, fit encoder, threshold tuning или отбора признаков.
4. PostgreSQL хранит metadata, статусы, связи, пути, хеши и отчеты, но не большие normalized/features/model-ready таблицы.
5. Parquet используется для normalized events, feature artifacts и model-ready artifacts.
6. DuckDB используется для аналитических SQL-проверок поверх Parquet.
7. Labels хранятся отдельно от X-признаков.
8. Leakage/source/label поля не попадают в model-ready X artifacts.
9. Все артефакты должны сохранять traceability.
10. Если label отсутствует, файл или событие нельзя считать benign по умолчанию.
11. Filename heuristic для TEST при label inference отключен в `LabelResolver`.
12. Отсутствующие timestamps нельзя синтетически заменять текущим временем.

## Основные CLI-команды

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers dns-analyze analyze-train-csv-content

python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers host-analyze analyze-csv-content

python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two normalize-all --branch host --limit 100
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Подробные аргументы и порядок запуска описаны в [cli_and_routing.md](cli_and_routing.md).
