# Отчет о создании документации по коду

Дата выполнения: 2026-06-22.

`PATH_REPORT` в текущем окружении не задан, поэтому отчет создан по относительному контракту:

```text
reports/ru/stage-two/code-documentation-report.md
```

## Созданные документы

Создан раздел:

```text
docs/ru/code-documentation/
```

Файлы:

| Документ | Назначение |
|---|---|
| `README.md` | индекс, карта раздела, инварианты, ключевые команды |
| `cli_and_routing.md` | `manage.py`, handlers routes, Stage Two CLI routes and arguments |
| `stage_one_handlers.md` | analyze/filter/sort/save/analyze/json handlers |
| `stage_two_overview.md` | Stage Two end-to-end pipeline |
| `storage_architecture.md` | `PATH_DATA_STORAGE`, storage tree, artifact paths |
| `postgresql_catalog.md` | catalog tables and traceability chain |
| `sqlalchemy_layer.md` | config/session/repositories/migrations/smoke check |
| `normalized_event_schema.md` | normalized event fields, timestamps, labels, JSON fields |
| `parser_strategy.md` | registry/resolver/parser classes/statuses |
| `label_resolver.md` | canonical label handling and TEST restrictions |
| `parquet_and_duckdb.md` | Parquet writer and DuckDB views/checks |
| `data_quality_checks.md` | DuckDB analytics and DataQualityChecker |
| `data_leakage_prevention.md` | forbidden X columns and leakage gates |
| `traceability.md` | model-ready to raw lineage |
| `dataset_contracts.md` | DNS/Host dataset contracts and counts |
| `extension_points.md` | adding handlers/parsers/schemas/labels/checks/stages |
| `risks_and_technical_debt.md` | limitations, gaps, risks, mitigations |

EN-документация не создавалась на этом шаге. Структура RU-раздела готова для последующего перевода.

## Покрытые разделы задачи

- обзор структуры проекта;
- CLI и routing layer;
- Stage One handlers;
- Stage Two pipeline;
- PostgreSQL Catalog;
- SQLAlchemy layer;
- normalized event schema;
- parser registry and parser strategy;
- label resolver;
- Parquet and DuckDB artifacts;
- data quality checks;
- leakage prevention;
- storage architecture;
- dataset-specific contracts;
- risks, limitations, technical debt;
- extension points;
- traceability chain.

## Проверенные команды и routes

Проверены по коду:

```text
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers dns-analyze <action>
python manage.py handlers host-analyze <action>
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready
python manage.py stage-two normalize-format
python manage.py stage-two normalize-all
python manage.py stage-two split-large-files
python manage.py stage-two normalize-dns [limit]
python manage.py stage-two normalize-host [limit]
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Аргументы Stage Two сверены по `scripts/stage_two/cli.py`.

## Проанализированные компоненты кода

| Компонент | Файлы |
|---|---|
| Entry point/router | `manage.py`, `scripts/router_script.py`, `scripts/handlers/router_handler.py`, `scripts/stage_two/cli.py` |
| Stage One | `scripts/handlers/analyze_dataset`, `filter_dataset`, `sort`, `save_sort`, `dns_analyze`, `host_analyze`, `json_handler` |
| Config | `config.py`, `scripts/db/config.py` |
| ORM/session | `scripts/db/session.py`, `scripts/db/models`, `scripts/db/repositories` |
| Migration | `scripts/db/migrations/versions/5a38996dff5f_create_stage_two_catalog_schema.py` |
| Storage | `scripts/stage_two/storage/bootstrap.py` |
| Ingestion | `scripts/stage_two/ingestion` |
| Parser registry | `scripts/stage_two/parser_registry`, `parser_registry_seed.json` |
| Parsers | `scripts/stage_two/parsers` |
| Normalization | `scripts/stage_two/normalization` |
| Labels | `scripts/stage_two/labels/resolver.py` |
| Parquet/DuckDB | `scripts/stage_two/parquet/writer.py`, `scripts/stage_two/duckdb/service.py` |
| Quality/leakage | `scripts/stage_two/quality/checkers.py`, `scripts/stage_two/model_ready/contracts.py` |
| Traceability | `scripts/stage_two/traceability/service.py` |
| Schemas | `schemas/normalized`, `schemas/features`, `schemas/model_ready` |
| Dataset docs | `docs/ru/analysis-dataset/**` |

## Проверки результата

Выполнены проверки:

- 17 Markdown-файлов созданы в `docs/ru/code-documentation`;
- `README.md` ссылается на все документы раздела;
- локальные Markdown-ссылки внутри раздела не имеют missing targets;
- все обязательные таблицы присутствуют в ORM models;
- все обязательные таблицы присутствуют в Alembic migration;
- parser registry seed разворачивается в 57 rows, недоступных parser classes не найдено;
- в документации явно зафиксировано, что missing labels не являются benign;
- TEST filename heuristic documented as disabled;
- labels/source/leakage fields documented as forbidden for model-ready X;
- absent timestamps documented as null/missing, not current time.

## Найденные ограничения

- `PATH_REPORT` не задан в текущем окружении; отчет создан under `reports/ru/stage-two`.
- EN-раздел `docs/en/code-documentation` не создавался.
- Feature/model-ready services есть, но полный end-to-end CLI для feature extraction/model-ready assembly не реализован.
- Stage One statuses могут отставать от Stage Two parser implementation; актуальное состояние parser coverage нужно проверять через `stage-two parser-coverage`.
- Host filter whitelist hardcoded в Python-коде.
- Host role fallback в `HostDatasetHandler` равен `TEST`, что требует осторожности при новых source paths.
- Некоторые source formats семантически неоднозначны, например `wls_day` в analysis docs описан как Windows log JSON-lines, а current seed маршрутизирует его через `HostNetflowParser`.

## Рекомендуемые follow-up задачи

1. Создать EN-перевод `docs/en/code-documentation`.
2. Вынести Host filter whitelist в версионированный config с тестами.
3. Добавить dedicated WLS parser или уточнить registry mapping для `wls_day`.
4. Реализовать CLI для feature extraction и model-ready build с обязательным leakage gate.
5. Регистрировать feature/model-ready schema versions аналогично normalized schema.
6. Добавить CI-проверку Markdown links, parser seed validation, leakage contracts и ORM/migration consistency.
7. Обновлять Stage One dataset statuses после добавления/изменения parser classes.
