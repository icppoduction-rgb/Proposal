# Proposal: единая документация проекта

Единый документ собран из русскоязычной документации `docs/ru/*` без удаления исходных разделов. Он сохраняет полный текст Markdown-источников, добавляет общую структуру и включает извлеченный текст `Project Proposal.docx` отдельным приложением.

> Документ сгенерирован из текущего состояния репозитория. При изменении файлов в `docs/ru/` этот файл нужно пересобрать или обновить вручную.

## Метаданные сборки

- Дата сборки: 2026-07-04.
- Markdown-источников: 47.
- DOCX-источников: 1.
- Основной язык: русский.
- Область: project overview, dataset analysis, Stage Two normalization, code documentation, proposal artifact.

## Как читать документ

1. Сначала прочитать обзор проекта, research context и QA/gaps.
2. Затем перейти к стратегии DNS/Host датасетов и карте признаков.
3. После этого читать анализ датасетов и readiness/label правила.
4. Для исполнения Stage Two использовать разделы normalization: команды, runbook, performance, storage, catalog, parser contracts, quality и leakage checks.
5. Для изменения кода использовать code documentation: routing, handlers, SQLAlchemy, parser strategy, extension points и technical debt.

## Ключевые инварианты

- Линия данных: `raw -> normalized -> features -> model-ready`.
- PostgreSQL catalog хранит metadata, статусы, lineage и ссылки на артефакты; большие таблицы остаются в Parquet/DuckDB layers.
- Traceability поля нужны для audit/debug, но не должны попадать в model-ready `X`.
- Labels должны быть отделены от признаков и проходить через явный resolver/mapping layer.
- TEST split используется только для финальной оценки и не должен участвовать в обучении, тюнинге или выборе thresholds.
- Любые parser/feature изменения должны сохранять обратную трассируемость к raw source и catalog records.

## Карта источников

### Обзор проекта и навигация

- [`docs/ru/README.md`](ru/README.md) - Документация проекта Proposal; строк: 144.
- [`docs/ru/project_documentation_index.md`](ru/project_documentation_index.md) - Индекс ключевой проектной документации; строк: 46.
- [`docs/ru/project_overview_and_research_context.md`](ru/project_overview_and_research_context.md) - Обзор проекта и research context; строк: 131.
- [`docs/ru/repository_state_qa_and_gaps.md`](ru/repository_state_qa_and_gaps.md) - Фактическое состояние репозитория, QA и gaps; строк: 144.

### Стратегия датасетов, признаки и proposal-level решения

- [`docs/ru/dataset_strategy_dns_host.md`](ru/dataset_strategy_dns_host.md) - Стратегия DNS и Host датасетов; строк: 145.
- [`docs/ru/feature_extraction_and_catalogue.md`](ru/feature_extraction_and_catalogue.md) - Feature extraction map и каталог признаков; строк: 189.

### Анализ датасетов

- [`docs/ru/analysis-dataset/README.md`](ru/analysis-dataset/README.md) - Анализ датасетов; строк: 78.
- [`docs/ru/analysis-dataset/source_inventory.md`](ru/analysis-dataset/source_inventory.md) - Индекс объединенных источников; строк: 71.
- [`docs/ru/analysis-dataset/dns_datasets.md`](ru/analysis-dataset/dns_datasets.md) - DNS datasets; строк: 56.
- [`docs/ru/analysis-dataset/host_datasets.md`](ru/analysis-dataset/host_datasets.md) - Host datasets; строк: 80.
- [`docs/ru/analysis-dataset/format_status_matrix.md`](ru/analysis-dataset/format_status_matrix.md) - Матрица форматов и статусов; строк: 96.
- [`docs/ru/analysis-dataset/labels_and_readiness.md`](ru/analysis-dataset/labels_and_readiness.md) - Labels и readiness; строк: 95.
- [`docs/ru/analysis-dataset/parser_feature_recommendations.md`](ru/analysis-dataset/parser_feature_recommendations.md) - Рекомендации для parser pipeline и feature extraction; строк: 93.

### Stage Two и нормализация

- [`docs/ru/normalization/README.md`](ru/normalization/README.md) - Stage Two / нормализация данных; строк: 111.
- [`docs/ru/normalization/usage_guide.md`](ru/normalization/usage_guide.md) - Руководство запуска Stage Two normalization; строк: 214.
- [`docs/ru/normalization/stage_two_commands.md`](ru/normalization/stage_two_commands.md) - Команды Stage Two normalization; строк: 497.
- [`docs/ru/normalization/runtime_resource_runbook.md`](ru/normalization/runtime_resource_runbook.md) - Runbook по runtime-ресурсам; строк: 271.
- [`docs/ru/normalization/performance_tuning.md`](ru/normalization/performance_tuning.md) - Настройка производительности normalization; строк: 259.
- [`docs/ru/normalization/storage_architecture.md`](ru/normalization/storage_architecture.md) - Архитектура storage Stage Two; строк: 120.
- [`docs/ru/normalization/postgresql_catalog_schema.md`](ru/normalization/postgresql_catalog_schema.md) - PostgreSQL Catalog и SQLAlchemy слой; строк: 196.
- [`docs/ru/normalization/parser_strategy.md`](ru/normalization/parser_strategy.md) - Стратегия parser registry и выбора parser; строк: 116.
- [`docs/ru/normalization/parser_development_guide.md`](ru/normalization/parser_development_guide.md) - Руководство добавления parser implementation; строк: 169.
- [`docs/ru/normalization/normalized_event_schema.md`](ru/normalization/normalized_event_schema.md) - Схема normalized event; строк: 130.
- [`docs/ru/normalization/label_resolver.md`](ru/normalization/label_resolver.md) - Разрешение labels; строк: 83.
- [`docs/ru/normalization/parquet_duckdb_artifacts.md`](ru/normalization/parquet_duckdb_artifacts.md) - Parquet и DuckDB артефакты; строк: 136.
- [`docs/ru/normalization/data_quality_checks.md`](ru/normalization/data_quality_checks.md) - Проверки качества данных; строк: 108.
- [`docs/ru/normalization/data_leakage_prevention.md`](ru/normalization/data_leakage_prevention.md) - Предотвращение data leakage; строк: 138.
- [`docs/ru/normalization/traceability.md`](ru/normalization/traceability.md) - Traceability и lineage; строк: 76.
- [`docs/ru/normalization/final_summary_template.md`](ru/normalization/final_summary_template.md) - Шаблон итоговой сводки Stage Two normalization; строк: 96.
- [`docs/ru/normalization/host_validation_wls_day_exclusion.md`](ru/normalization/host_validation_wls_day_exclusion.md) - Исключение Host VALIDATION wls_day; строк: 20.

### Документация по коду

- [`docs/ru/code-documentation/README.md`](ru/code-documentation/README.md) - Документация по коду проекта; строк: 114.
- [`docs/ru/code-documentation/cli_and_routing.md`](ru/code-documentation/cli_and_routing.md) - CLI и слой routing; строк: 213.
- [`docs/ru/code-documentation/stage_one_handlers.md`](ru/code-documentation/stage_one_handlers.md) - Handlers Stage One; строк: 308.
- [`docs/ru/code-documentation/stage_two_overview.md`](ru/code-documentation/stage_two_overview.md) - Обзор Stage Two; строк: 354.
- [`docs/ru/code-documentation/storage_architecture.md`](ru/code-documentation/storage_architecture.md) - Архитектура storage; строк: 156.
- [`docs/ru/code-documentation/sqlalchemy_layer.md`](ru/code-documentation/sqlalchemy_layer.md) - Слой SQLAlchemy; строк: 171.
- [`docs/ru/code-documentation/postgresql_catalog.md`](ru/code-documentation/postgresql_catalog.md) - PostgreSQL Catalog; строк: 205.
- [`docs/ru/code-documentation/parser_strategy.md`](ru/code-documentation/parser_strategy.md) - Стратегия парсеров; строк: 145.
- [`docs/ru/code-documentation/normalized_event_schema.md`](ru/code-documentation/normalized_event_schema.md) - Схема normalized event; строк: 172.
- [`docs/ru/code-documentation/label_resolver.md`](ru/code-documentation/label_resolver.md) - Разрешение labels; строк: 151.
- [`docs/ru/code-documentation/parquet_and_duckdb.md`](ru/code-documentation/parquet_and_duckdb.md) - Parquet и DuckDB артефакты; строк: 131.
- [`docs/ru/code-documentation/data_quality_checks.md`](ru/code-documentation/data_quality_checks.md) - Проверки качества данных; строк: 107.
- [`docs/ru/code-documentation/data_leakage_prevention.md`](ru/code-documentation/data_leakage_prevention.md) - Предотвращение data leakage; строк: 129.
- [`docs/ru/code-documentation/dataset_contracts.md`](ru/code-documentation/dataset_contracts.md) - Dataset-specific contracts; строк: 109.
- [`docs/ru/code-documentation/extension_points.md`](ru/code-documentation/extension_points.md) - Точки расширения; строк: 165.
- [`docs/ru/code-documentation/traceability.md`](ru/code-documentation/traceability.md) - Трассируемость; строк: 88.
- [`docs/ru/code-documentation/risks_and_technical_debt.md`](ru/code-documentation/risks_and_technical_debt.md) - Риски, ограничения и technical debt; строк: 70.

- [`docs/ru/Project Proposal.docx`](<ru/Project Proposal.docx>) - исходный DOCX proposal artifact; размер: 640724 байт.

---

## Обзор проекта и навигация

### Источник: `docs/ru/README.md`

[Открыть исходный файл](ru/README.md)

#### Документация проекта Proposal

Этот README является общей точкой входа в документацию проекта. Он помогает быстро найти материалы по исследовательскому контексту, Stage One, Stage Two normalization, архитектуре кода, датасетам, PostgreSQL Catalog, Parquet/DuckDB, labels, features и leakage checks.

Документация разделяет:

- **фактическую реализацию** - то, что подтверждено текущим кодом и CLI;
- **операционные инструкции** - как запускать и проверять pipeline;
- **исследовательские материалы и proposal** - цели, методология, dataset strategy, feature catalogue и планы;
- **gaps и follow-up** - то, что еще не реализовано или требует уточнения.

##### Синхронизация с текущим кодом

Последняя сверка с кодом: 2026-07-04.

- Маршрутизация Stage Two реализована в `scripts/stage_two/cli.py`; этот файл является главным источником истины по поддержанным `stage-two` командам.
- Fallback-список команд из `config.manage_commands`, который печатается при некоторых ошибках запуска, старше фактического router и не показывает все текущие Stage Two команды, включая `parser-coverage`, `mark-ready`, `normalize-format`, `normalize-all`, `benchmark-normalization` и `split-large-files`.
- Runtime defaults без resource profile консервативные: `workers=1`, `batch_size=50000`, `max_output_part_rows=50000`. Resource profiles и format policy для `normalize-format` могут изменить итоговые значения перед запуском.
- Services для feature/model-ready writer/registry уже есть, но полный CLI для end-to-end feature extraction, model-ready build, model training и evaluation пока остается follow-up/proposal work.

##### Быстрый старт

| Если нужно | Читать |
| --- | --- |
| Понять весь проект и исследовательский контекст | [project_overview_and_research_context.md](ru/project_overview_and_research_context.md) |
| Увидеть карту ключевых документов | [project_documentation_index.md](ru/project_documentation_index.md) |
| Проверить, что реализовано, а что пока proposal | [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) |
| Разобраться в структуре кода и CLI | [code-documentation/README.md](ru/code-documentation/README.md) |
| Найти Stage One анализ датасетов | [analysis-dataset/README.md](ru/analysis-dataset/README.md) |
| Запустить Stage Two normalization | [normalization/README.md](ru/normalization/README.md), [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md) |
| Выбрать DNS/Host стратегию и split roles | [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md) |
| Смотреть feature engineering и leakage exclusions | [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) |

##### Основные разделы

| Раздел | Назначение | Тип |
| --- | --- | --- |
| [analysis-dataset/](ru/analysis-dataset/README.md) | Результаты Stage One анализа DNS/Host buckets, counts, formats, labels, readiness и parser recommendations. | Фактический анализ датасетов |
| [code-documentation/](ru/code-documentation/README.md) | Архитектура кода: CLI/routing, Stage One handlers, Stage Two, PostgreSQL Catalog, SQLAlchemy, schemas, parsers, labels, Parquet/DuckDB, checks, risks. | Техническая документация по коду |
| [normalization/](ru/normalization/README.md) | Operational guide по Stage Two normalization: storage, catalog ingestion, parser registry, `READY_FOR_PARSING`, normalization commands, DuckDB/leakage checks, traceability. | Фактическая реализация и runbooks |
| [project_documentation_index.md](ru/project_documentation_index.md) | Индекс верхнеуровневых документов и карта переноса старых материалов. | Навигация |
| [project_overview_and_research_context.md](ru/project_overview_and_research_context.md) | Research context, цели, methodology, proposal-level architecture и ограничения. | Research/proposal |
| [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md) | DNS/Host dataset strategy с явным разделением `TRAIN`, `VALIDATION`, `TEST`. | Dataset strategy |
| [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) | Feature extraction map, feature groups, schema requirements, forbidden leakage fields, implementation priorities. | Feature engineering |
| [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) | Подтвержденная реализация, proposal-level gaps, QA и follow-up tasks. | QA/gaps |
| [Project Proposal.docx](<ru/Project Proposal.docx>) | Русская версия проектного proposal-документа в DOCX. | Research/proposal artifact |

##### Где искать по темам

###### Stage One

- [code-documentation/stage_one_handlers.md](ru/code-documentation/stage_one_handlers.md) - handlers `analyze_dataset`, `filter_dataset`, `sort`, `save_sort`, `dns_analyze`, `host_analyze`, JSON manager.
- [analysis-dataset/README.md](ru/analysis-dataset/README.md) - итоговый индекс анализа датасетов.
- [analysis-dataset/dns_datasets.md](ru/analysis-dataset/dns_datasets.md) - DNS `TRAIN` / `VALIDATION` / `TEST`.
- [analysis-dataset/host_datasets.md](ru/analysis-dataset/host_datasets.md) - Host `TRAIN` / `VALIDATION` / `TEST`.
- [analysis-dataset/format_status_matrix.md](ru/analysis-dataset/format_status_matrix.md) - readiness matrix по 64 format buckets.
- [analysis-dataset/labels_and_readiness.md](ru/analysis-dataset/labels_and_readiness.md) - labels, readiness statuses и anti-leakage правила.

###### Stage Two / Normalization

- [normalization/README.md](ru/normalization/README.md) - границы Stage Two, основные команды, инварианты.
- [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md) - полный reference по Stage Two commands: входы, выходы, PostgreSQL statuses, ошибки и проверки.
- [normalization/usage_guide.md](ru/normalization/usage_guide.md) - общий порядок запуска CLI.
- [normalization/runtime_resource_runbook.md](ru/normalization/runtime_resource_runbook.md) - эксплуатация, recovery и large-file сценарии.
- [normalization/performance_tuning.md](ru/normalization/performance_tuning.md) - `workers`, `batch-size`, `max-output-part-rows`, packet modes.

###### Архитектура кода

- [code-documentation/README.md](ru/code-documentation/README.md) - карта технической документации.
- [code-documentation/cli_and_routing.md](ru/code-documentation/cli_and_routing.md) - `manage.py`, routing layer, Stage One/Stage Two commands.
- [code-documentation/stage_two_overview.md](ru/code-documentation/stage_two_overview.md) - Stage Two pipeline.
- [code-documentation/extension_points.md](ru/code-documentation/extension_points.md) - как расширять handlers, parsers, schemas, labels, checks и stages.
- [code-documentation/risks_and_technical_debt.md](ru/code-documentation/risks_and_technical_debt.md) - known limitations, parser gaps, leakage/timestamp/large-file risks.

###### PostgreSQL Catalog и SQLAlchemy

- [code-documentation/postgresql_catalog.md](ru/code-documentation/postgresql_catalog.md) - catalog tables и traceability chain.
- [code-documentation/sqlalchemy_layer.md](ru/code-documentation/sqlalchemy_layer.md) - config, session, models, repositories, migrations.
- [normalization/postgresql_catalog_schema.md](ru/normalization/postgresql_catalog_schema.md) - Stage Two catalog schema с точки зрения normalization.

###### Schemas, Parsers и Labels

- [code-documentation/normalized_event_schema.md](ru/code-documentation/normalized_event_schema.md) - normalized event schema.
- [normalization/normalized_event_schema.md](ru/normalization/normalized_event_schema.md) - operational schema guide для normalization.
- [code-documentation/parser_strategy.md](ru/code-documentation/parser_strategy.md) и [normalization/parser_strategy.md](ru/normalization/parser_strategy.md) - parser registry/resolver strategy.
- [normalization/parser_development_guide.md](ru/normalization/parser_development_guide.md) - добавление нового parser implementation.
- [code-documentation/label_resolver.md](ru/code-documentation/label_resolver.md) и [normalization/label_resolver.md](ru/normalization/label_resolver.md) - label sources, `TEST` restrictions, conflicts.

###### Parquet, DuckDB, Quality и Leakage

- [code-documentation/parquet_and_duckdb.md](ru/code-documentation/parquet_and_duckdb.md) - Parquet paths, writer, DuckDB views/checks.
- [normalization/parquet_duckdb_artifacts.md](ru/normalization/parquet_duckdb_artifacts.md) - artifacts и DuckDB usage в Stage Two.
- [normalization/data_quality_checks.md](ru/normalization/data_quality_checks.md) - DataQuality/DuckDB checks.
- [normalization/data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md) - forbidden X columns и anti-leakage invariants.
- [code-documentation/traceability.md](ru/code-documentation/traceability.md) и [normalization/traceability.md](ru/normalization/traceability.md) - `raw -> normalized -> features -> model-ready`.

###### Features и исследовательские материалы

- [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) - feature groups, contracts, exclusions и priorities.
- [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md) - dataset roles, sources, strategy и limitations.
- [project_overview_and_research_context.md](ru/project_overview_and_research_context.md) - research framing и proposal-level архитектура.
- [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) - где proposal расходится с текущей реализацией.

##### Рекомендуемый порядок чтения

1. [project_documentation_index.md](ru/project_documentation_index.md) - общий индекс и карта объединенных документов.
2. [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) - граница между реализованным и proposal.
3. [analysis-dataset/README.md](ru/analysis-dataset/README.md) - фактическая структура DNS/Host данных.
4. [code-documentation/README.md](ru/code-documentation/README.md) - архитектура кода и pipeline.
5. [normalization/README.md](ru/normalization/README.md) - Stage Two implementation guide.
6. [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md) - точные команды запуска.
7. [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) - feature engineering и model-ready ограничения.

##### Основные инварианты

1. Raw-файлы не изменяются.
2. `TRAIN`, `VALIDATION` и `TEST` не смешиваются.
3. `TEST` не используется для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
4. PostgreSQL хранит metadata, статусы, связи, пути, хеши и отчеты; большие normalized/features/model-ready таблицы хранятся в Parquet.
5. Labels не являются input features.
6. Leakage/source/label fields не попадают в model-ready X artifacts.
7. Отсутствующий label не означает benign.
8. Отсутствующий timestamp нельзя заменять текущим временем.
9. Traceability должна сохраняться по цепочке `raw -> normalized -> features -> model-ready`.
##### Stage Two performance quick start

Для текущей performance architecture используйте:

- [normalization/performance_tuning.md](ru/normalization/performance_tuning.md) - resource profiles, format policy, benchmark target и troubleshooting.
- [normalization/runtime_resource_runbook.md](ru/normalization/runtime_resource_runbook.md) - operational sequence для benchmark/full runs и recovery.
- [normalization/stage_two_commands.md](ru/normalization/stage_two_commands.md) - точный CLI reference, включая `benchmark-normalization`.
- [code-documentation/stage_two_overview.md](ru/code-documentation/stage_two_overview.md) - execution planner, bounded multiprocessing, chunking, atomic Parquet, benchmark и validation architecture.

Рекомендуемый flow:

```bash
python manage.py stage-two benchmark-normalization --branch host --role TEST --format txt --limit 10000 --sample-ratio 0.10 --resource-profile fast
python manage.py stage-two normalize-format --branch host --role TEST --format txt --resource-profile fast --resume
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Начинайте с `safe` или `balanced`; используйте `fast` или `aggressive` только после чистых benchmark reports и quality gates.

---

### Источник: `docs/ru/project_documentation_index.md`

[Открыть исходный файл](ru/project_documentation_index.md)

#### Индекс ключевой проектной документации

Этот индекс заменяет набор разрозненных документов верхнего уровня и показывает, куда перенесена ключевая информация по proposal, стратегиям датасетов, feature engineering и фактическому состоянию репозитория.

##### Итоговая структура

| Документ | Назначение |
| --- | --- |
| [project_overview_and_research_context.md](ru/project_overview_and_research_context.md) | Research context, proposal-level архитектура, вопросы, цели, methodology, scope, план и ограничения. |
| [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md) | Единая стратегия DNS и Host датасетов с явным разделением `TRAIN` / `VALIDATION` / `TEST`. |
| [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md) | Карта feature extraction, каталог групп признаков, schema requirements, leakage exclusions и приоритеты реализации. |
| [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md) | Что подтверждено текущим кодом, что остается proposal/планом, QA по разделам 3.3-3.8, gaps и follow-up. |

##### Объединенные старые документы

| Старый документ | Куда перенесено содержание |
| --- | --- |
| `project_proposal_analysis.md` | `project_overview_and_research_context.md`, `repository_state_qa_and_gaps.md`. |
| `functional_project_cheatsheet.md` | `project_overview_and_research_context.md`, `dataset_strategy_dns_host.md`, `feature_extraction_and_catalogue.md`. |
| `dns_dataset_strategy.md` | `dataset_strategy_dns_host.md`. |
| `host_datasets_analysis.md` | `dataset_strategy_dns_host.md`, `repository_state_qa_and_gaps.md`. |
| `dataset_feature_extraction_map.md` | `feature_extraction_and_catalogue.md`, `dataset_strategy_dns_host.md`. |
| `feature_catalogue_full.md` | `feature_extraction_and_catalogue.md`. |
| `repository_qa_section_3_8.md` | `repository_state_qa_and_gaps.md`. |

##### Связанные актуальные разделы

- [analysis-dataset/README.md](ru/analysis-dataset/README.md) — фактический Stage One анализ bucket/formats/readiness.
- [normalization/README.md](ru/normalization/README.md) — Stage Two normalization guide.
- [code-documentation/README.md](ru/code-documentation/README.md) — архитектура кода, CLI, Stage One/Stage Two, DB и parser strategy.

##### Правила чтения

1. Для research proposal читать сначала [project_overview_and_research_context.md](ru/project_overview_and_research_context.md).
2. Для выбора датасетов читать [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md).
3. Для реализации feature engineering читать [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md).
4. Для сверки с текущим кодом читать [repository_state_qa_and_gaps.md](ru/repository_state_qa_and_gaps.md).

##### Архитектурные инварианты

- `TRAIN`, `VALIDATION` и `TEST` не смешиваются.
- `TEST` не используется для training, fit preprocessing, feature selection или threshold tuning.
- DNS и Host логика разделены; объединение выполняется только на уровне normalized events, windows, features и traceability.
- Labels являются target/audit fields, а не input features.
- Отсутствие label не означает benign.
- Proposal-level идеи не считаются реализованными, пока они не подтверждены кодом, артефактами или Stage Two документацией.

---

### Источник: `docs/ru/project_overview_and_research_context.md`

[Открыть исходный файл](ru/project_overview_and_research_context.md)

#### Обзор проекта и research context

Документ объединяет сведения из `project_proposal_analysis.md` и `functional_project_cheatsheet.md`. Он описывает proposal-level замысел проекта и отделяет исследовательский план от фактической реализации репозитория.

##### Назначение

Проект посвящен теме **Behaviour-driven hybrid learning for data exfiltration detection**. Цель исследования — спроектировать и оценить гибридный ML/DL framework для обнаружения многоэтапной эксфильтрации данных с использованием:

- DNS и network признаков;
- host-level telemetry;
- behavioural sequence modelling;
- explainability через SHAP;
- role-separated dataset strategy для `TRAIN`, `VALIDATION`, `TEST`.

##### Research gap

Исходные документы фиксируют один и тот же исследовательский разрыв:

| Ограничение существующих подходов | Последствие |
| --- | --- |
| Single-modality detection: только network или только host. | Модель видит неполный жизненный цикл атаки. |
| Event-level classification без последовательностей. | Многоэтапная эксфильтрация может быть обнаружена поздно или фрагментарно. |
| Слабая explainability. | SOC analyst не видит, какие признаки привели к решению. |
| Несовместимость публичных датасетов. | Нельзя безоговорочно выполнять raw fusion host/network логов. |

Вывод: multi-source integration должна выполняться на уровне признаков, временных окон, normalized events и traceability, а не через механическое объединение raw logs.

##### Proposal-level архитектура

```mermaid
flowchart TD
    A["DNS/network datasets"] --> D["Multi-source feature integration"]
    B["Host telemetry datasets"] --> D
    C["Stage Two normalization"] --> D
    D --> E["Hybrid ML/DL classification: RF, XGBoost, CNN"]
    D --> F["Behavioural sequence modelling: LSTM"]
    E --> G["Late fusion"]
    F --> G
    G --> H["Detection decision"]
    H --> I["SHAP explanations"]
```

| Слой | Назначение | Статус |
| --- | --- | --- |
| Multi-source integration | Нормализация host/network признаков в единое представление. | Proposal / Stage Two design target. |
| Hybrid ML/DL classification | Random Forest, XGBoost, CNN для structured/local feature patterns. | Proposal; модельный код не подтвержден. |
| Behavioural sequence modelling | LSTM по ordered event sequences. | Proposal; sequence builder/model code не подтвержден. |
| Late fusion | Агрегация вероятностей classifier и sequence model. | Proposal; веса/формула не заданы. |
| SHAP explainability | Global/local explanations и rank-order consistency. | Proposal; SHAP variants не зафиксированы. |

##### Research questions

| ID | Вопрос | Что должен дать для реализации |
| --- | --- | --- |
| RQ1 | Какие cross-domain признаки host/network характеризуют стадии эксфильтрации? | Feature catalogue и dataset-feature map. |
| RQ2 | Как объединить classical ML и DL в hybrid architecture? | Baseline classifiers, CNN branch, сравнение ablation. |
| RQ3 | Как встроить behavioural sequence modelling? | Sequence window builder, LSTM branch, event ordering. |
| RQ4 | Как XAI повышает interpretability и помогает расследованию? | SHAP reports, fold consistency, case studies. |

##### Aim and objectives

Цель: разработать и оценить behaviour-driven hybrid ML framework для обнаружения data exfiltration, объединяющий host telemetry, network features, behavioural sequence modelling и explainable AI.

Задачи:

1. Определить host-level и network-level признаки для data exfiltration detection.
2. Спроектировать hybrid ML/DL detection architecture: RF, XGBoost, CNN, LSTM.
3. Реализовать behavioural sequence modelling для temporal attack patterns.
4. Интегрировать SHAP-based explainability.
5. Оценить framework на public cybersecurity benchmark datasets.

##### Scope

| Входит в scope | Вне текущего scope |
| --- | --- |
| Public benchmark datasets. | Live traffic capture. |
| RF, XGBoost, CNN, LSTM. | RL components. |
| Feature-level host/network integration. | Large-scale raw multi-dataset fusion. |
| Supervised/semi-supervised sequence modelling. | Fully unsupervised sequence modelling. |
| SHAP explainability. | Полная SOC product integration. |

##### Methodology

Proposal использует **Design Science Research (DSR)**:

1. Feature identification and dataset preparation.
2. Hybrid framework design.
3. Behavioural sequence modelling.
4. Explainability integration.
5. Evaluation and validation.

Плановый timeline: 12 недель, май-август 2026.

| Фаза | Key deliverable | Целевая дата |
| --- | --- | --- |
| Phase 1 | Preprocessed feature dataset with MITRE ATT&CK mappings. | May 15 |
| Phase 2 | Hybrid detection framework prototype. | June 12 |
| Phase 3 | Integrated LSTM sequence modelling component. | July 3 |
| Phase 4 | SHAP explanation module. | July 24 |
| Phase 5 | Experimental results report with comparative analysis. | August 14 |
| Report writing | Completed report and slides. | August 28 |

##### Evaluation plan

| Элемент | Proposal-level решение | Gap реализации |
| --- | --- | --- |
| Metrics | Accuracy, precision, recall, F1-score, FPR, AUC. | Модельный evaluation код не подтвержден. |
| Validation | Stratified k-fold cross-validation. | Значение `k` не задано. |
| Ablation | Full hybrid vs individual components. | Ablation experiments не реализованы. |
| Baselines | RF only, XGBoost only, CNN only, LSTM only, hybrid without SHAP. | Конкретные baseline configs отсутствуют. |
| Explainability | SHAP explanations for TP/FP and fold rank stability. | TreeSHAP/DeepSHAP/KernelSHAP не выбраны. |

##### Proposal risks

| Риск | Последствие | Митигирующая мера |
| --- | --- | --- |
| Несовместимость host и network datasets. | Нельзя доказать прямую raw-level корреляцию. | Использовать feature-level integration и явно документировать ограничения. |
| Class imbalance. | Accuracy может быть вводящей в заблуждение. | Делать precision/recall/F1 основными метриками. |
| Sequence model underperformance. | LSTM может не улучшить baseline. | Добавить temporal aggregation fallback и ablation. |
| Compute constraints. | DL experiments могут быть ограничены. | Использовать Colab/Kaggle или упрощенные модели. |
| Weak explainability design. | SHAP может объяснять proxy/leakage признаки. | Исключить leakage fields и проверять SHAP stability. |

##### Что является фактом, а что proposal

| Категория | Статус |
| --- | --- |
| Stage One dataset preparation, sorting, JSON path maps. | Подтверждено текущим репозиторием. |
| Stage Two normalization/catalog/parquet/parser design. | Частично реализовано/задокументировано в Stage Two документации; проверять по коду. |
| RF/XGBoost/CNN/LSTM training. | Proposal-level, в QA документе модельная реализация не подтверждена. |
| SHAP explanations. | Proposal-level. |
| Feature catalogue. | Архитектурный контракт для будущей реализации feature extraction. |

---

### Источник: `docs/ru/repository_state_qa_and_gaps.md`

[Открыть исходный файл](ru/repository_state_qa_and_gaps.md)

#### Фактическое состояние репозитория, QA и gaps

Документ объединяет `repository_qa_section_3_8.md`, QA-блоки из `project_proposal_analysis.md` и ограничения из `functional_project_cheatsheet.md`. Его задача — отделить реализованное состояние репозитория от proposal-level планов.

##### Scope анализа

Исходный QA документ фиксировал просмотр репозитория (`scripts`, `docs`, `report`, `planning`, `temp_data`, `logs`, конфиги). Ключевой вывод сохраняется:

> В текущем репозитории подтвержден этап подготовки датасетов, а не обучение/оценка моделей.

##### Что подтверждено текущей реализацией

| Область | Подтверждено |
| --- | --- |
| Stage One dataset preparation | Сканирование датасетов, назначение ролей, фильтрация host, сортировка по форматам, JSON path maps. |
| DNS datasets | `CIC-Bell-DNS-2021` (`TRAIN` + `VALIDATION`), `CIC-Bell-DNS-EXF-2021` (`TRAIN`), `Mendeley-DNS-Exfiltration-Dataset` (`TEST`). |
| Host datasets | `TRAIN`: ADFA IDS, LID-DS 2021, Maintainable Log Dataset; `VALIDATION`: LID-DS 2019, LANL, Windows Event Log / OTRF; `TEST`: Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network / LANL. |
| Pipeline separation | DNS и Host обрабатываются отдельными ветками. |
| Confirmed volumes | DNS sorted/exported files: 35; Host filtered kept paths: 361646 в старом QA, 361670 total files по актуальной analysis-dataset сводке с 64 buckets. |
| Stage Two normalization | Реализованные CLI routes покрывают storage bootstrap, catalog ingestion, parser registry seed, parser coverage, mark-ready, normalization точного bucket, benchmark runs, splitting больших line-based files, DuckDB checks, leakage checks и traceability. |
| Feature/model-ready services | Contracts и writer/registry services есть в `scripts/stage_two/features` и `scripts/stage_two/model_ready`, но полный end-to-end orchestration не опубликован через `manage.py`. |
| Current docs | Stage One/Stage Two architecture, normalization, parser strategy, labels, leakage, performance controls и traceability задокументированы в `analysis-dataset/`, `normalization/`, `code-documentation/`. |

##### Что является proposal/планом, а не подтвержденной реализацией

| Область | Proposal-level утверждение | Gap |
| --- | --- | --- |
| ML preprocessing | Missing value handling, scaling, categorical encoding. | В коде не подтверждены `MinMaxScaler`, `StandardScaler`, encoders или preprocessing fit pipeline. |
| Class imbalance | SMOTE/undersampling/class weights. | Реализация не найдена. |
| Random Forest / XGBoost | Baseline classifiers. | Параметры, training code и tuning не зафиксированы. |
| CNN | Deep learning branch for local feature patterns. | Архитектура не указана. |
| LSTM | Sequence-level binary classification, 50-100 events per sequence. | Sequence builder, step/overlap, alignment и model config не реализованы. |
| Late fusion | Aggregation of classifier + sequence probabilities. | Формула/веса/threshold не заданы. |
| SHAP | Feature attribution and rank stability. | TreeSHAP/DeepSHAP/KernelSHAP не выбраны и не реализованы. |
| Evaluation | Stratified k-fold CV, ablation, baseline comparisons. | Значение `k`, statistical tests, seeds и reports не зафиксированы. |
| Runtime environment | Cloud fallback, hardware assumptions. | Hardware, Python/lib versions для ML stack не указаны; `requirements.txt` содержит только `python-dotenv` и `rich` без версий. |

##### Текущие замечания по реализации

Сверено с кодом 2026-07-04:

- Stage Two routing находится в `scripts/stage_two/cli.py`; `config.manage_commands` является старым печатным списком команд и не полон для текущего Stage Two.
- `normalize-format` и `benchmark-normalization` перед запуском применяют resource profiles и format-specific runtime policy. `normalize-all` получает общие runtime options, но не применяет per-format policy на уровне CLI route.
- Реализованные quality gates: parser reports, post-run validation для `normalize-format`, DuckDB checks, leakage checks и traceability lookup. Это проверки вокруг normalized/features/model-ready artifacts, а не полный ML experiment pipeline.
- Репозиторий по-прежнему не подтверждает RF/XGBoost/CNN/LSTM training, preprocessing fit/transform orchestration, feature extraction CLI, model-ready build CLI, SHAP analysis или evaluation reports.

##### QA по разделам proposal 3.3-3.8

###### Dataset Selection

| Вопрос | Ответ |
| --- | --- |
| Какие датасеты использовались? | DNS и Host datasets перечислены в [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md). |
| Есть ли total samples / class split / feature count? | Для большинства источников нет подтвержденных чисел. Для `CIC-Bell-DNS-2021` указано около 1,000,000 доменов и около 99% benign как утверждение документации. |
| Network и Host — отдельные датасеты? | Да, отдельные datasets и отдельные pipelines. |
| Host features симулировались из network? | В коде такой реализации не найдено; в proposal это только возможная feature-level simulation при отсутствии paired данных. |

###### Data Preprocessing

| Вопрос | Ответ |
| --- | --- |
| Missing values | Реализация обработки model-feature пропусков не подтверждена. |
| Normalization/scaling | Не найдено. |
| Categorical encoding | Не найдено. |
| Train/test split | Числовой split не задан; есть role-based strategy и плановая stratified k-fold CV. |

###### Class Imbalance

Методы SMOTE, undersampling, class weights или аналогичные механизмы не подтверждены кодом.

###### Model Architecture

| Модель | Состояние |
| --- | --- |
| Random Forest | Proposal-level; параметры/tuning не указаны. |
| XGBoost | Proposal-level; параметры/tuning не указаны. |
| CNN | Proposal-level; архитектура не указана. |
| LSTM | Proposal-level; есть только идея sequence-level binary classification. |

###### Sequence Construction

| Вопрос | Состояние |
| --- | --- |
| Sequence length | Proposal указывает 50-100 событий. |
| Window step / overlap | Не задано. |
| Multi-modal time alignment | Явный алгоритм не найден. |
| Labels for sequence windows | План: label based on exfiltration activity within window; implementation не подтверждена. |

###### Decision Fusion

Proposal говорит о **late fusion** через агрегацию вероятностей classification и sequence components. Веса, формула и threshold policy не указаны.

###### SHAP

Упоминается SHAP-based feature attribution. Не указано:

- TreeSHAP для RF/XGBoost;
- DeepSHAP для CNN/LSTM;
- KernelSHAP fallback;
- способ explainability для sequence windows.

###### Experimental Environment

| Параметр | Состояние |
| --- | --- |
| Number of CV folds | Не указан. |
| Statistical tests | Не указаны. |
| Hardware | Не указан. |
| Software versions | ML stack не зафиксирован. |
| Random seed | Не указан. |

##### Риски и рекомендации

| Риск | Где возникает | Последствие | Рекомендация |
| --- | --- | --- | --- |
| Host/network dataset incompatibility | Dataset strategy / hybrid architecture. | Нельзя доказать raw-level correlation. | Использовать feature-level integration, явно документировать assumptions. |
| TEST leakage | Feature extraction / model-ready artifacts. | Завышенная оценка качества. | Запретить TEST для training, fit preprocessing, feature selection, threshold tuning. |
| Label leakage | Filename/scenario/path fields. | Модель учит источник, а не поведение. | Исключать label/source/path/scenario fields из X. |
| Weak labels | Filename, IDS alert, scenario metadata. | Неверная supervised target разметка. | Использовать `label_status`, confidence и mapping rules. |
| Missing timestamps | TXT/trace/binary sources. | Неверные temporal features. | Использовать `timestamp=null`, `timestamp_type=missing` или event order; не подставлять current time. |
| Large files | PCAP, BSON, JSON, netflow, txt traces. | Memory/performance failures. | Streaming parsers, batch writes, DuckDB/Parquet checks. |
| Schema drift | Mixed CSV/JSON/log schemas. | Broken normalization/features. | Schema-aware parsers и per-format quality reports. |
| Explainability over proxy fields | SHAP / model-ready X. | Объяснения будут misleading. | Leakage checks перед SHAP, separate audit fields. |

##### Follow-up tasks

1. Зафиксировать `feature_catalog.yml/json` как machine-readable contract.
2. Реализовать Stage Two feature extraction layers по [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md).
3. Добавить preprocessing contracts: missing values, categorical encoding, scaling, fit/transform separation.
4. Добавить model configs для RF/XGBoost/CNN/LSTM.
5. Описать sequence window policy: length, step, overlap, label assignment, time alignment.
6. Описать late fusion formula и threshold policy.
7. Выбрать SHAP variants по model family.
8. Добавить experiment config: CV folds, random seeds, hardware/software versions, statistical tests.
9. Расширить data quality reports: class balance, label coverage, timestamp coverage, schema drift, leakage.

##### Связанные документы

- [project_overview_and_research_context.md](ru/project_overview_and_research_context.md)
- [dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md)
- [feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md)
- [analysis-dataset/README.md](ru/analysis-dataset/README.md)
- [normalization/README.md](ru/normalization/README.md)
- [code-documentation/README.md](ru/code-documentation/README.md)

---

## Стратегия датасетов, признаки и proposal-level решения

### Источник: `docs/ru/dataset_strategy_dns_host.md`

[Открыть исходный файл](ru/dataset_strategy_dns_host.md)

#### Стратегия DNS и Host датасетов

Документ объединяет `dns_dataset_strategy.md`, `host_datasets_analysis.md`, dataset role sections из `functional_project_cheatsheet.md` и карту датасетов из `dataset_feature_extraction_map.md`. DNS и Host логика разделены явно; `TRAIN`, `VALIDATION` и `TEST` не смешиваются.

##### Назначение

Стратегия датасетов нужна для трех задач:

1. Обосновать proposal-level выбор источников данных.
2. Зафиксировать role matrix для обучения, валидации и финального тестирования.
3. Подготовить Stage Two parser pipeline и feature extraction к разным типам телеметрии.

##### Общие правила

- `TRAIN` используется для обучения и fit preprocessing.
- `VALIDATION` используется для настройки, контроля false positives и проверки устойчивости.
- `TEST` используется только для финальной evaluation/inference.
- DNS и Host не объединяются на raw-level.
- Hybrid integration выполняется на уровне normalized events, windows, feature artifacts и traceability.
- Экспериментальные датасеты не повышаются до `TRAIN` без отдельного решения.

##### DNS strategy

Текущий DNS scope включает три активных источника. DNS `EXPERIMENTS` в исходной стратегии не используются.

| Роль | Датасет | Назначение | Источник |
| --- | --- | --- | --- |
| `TRAIN` | CIC-Bell-DNS-EXF-2021 | Обучение attack-class behavior: DNS exfiltration / tunneling. | <https://www.unb.ca/cic/datasets/dns-exf-2021.html> |
| `TRAIN` | CIC-Bell-DNS-2021 | Benign baseline и обучение нормальному DNS-поведению. | <https://www.unb.ca/cic/datasets/dns-2021.html> |
| `VALIDATION` | Split CIC-Bell-DNS-2021 | Контроль false positives и настройка threshold. | <https://www.unb.ca/cic/datasets/dns-2021.html> |
| `TEST` | Mendeley DNS Exfiltration Dataset | Независимая проверка generalization и междатасетного переноса. | <https://data.mendeley.com/datasets/c4n7fckkz3/3> |

```text
DNS TRAIN:
  - CIC-Bell-DNS-EXF-2021
  - CIC-Bell-DNS-2021

DNS VALIDATION:
  - split CIC-Bell-DNS-2021

DNS TEST:
  - Mendeley DNS Exfiltration Dataset
```

###### DNS feature purpose

| Датасет | Attack lifecycle | Основные feature groups |
| --- | --- | --- |
| CIC-Bell-DNS-EXF-2021 | Exfiltration | DNS lexical, entropy, temporal, RR/TTL, stateful/stateless DNS features. |
| CIC-Bell-DNS-2021 | Benign baseline / exfiltration contrast | Те же DNS признаки; используется для normal DNS baseline и FP-control. |
| Mendeley DNS Exfiltration Dataset | Exfiltration / generalization | DNS lexical, temporal, numeric feature table, source IP windows. |

##### Host strategy

Host-side часть не должна опираться на один датасет, потому что разные источники покрывают разные уровни поведения:

- system calls;
- enterprise logs;
- authentication events;
- Windows/Sysmon telemetry;
- malware traces;
- cloud telemetry;
- host + network events.

###### Host role matrix

| Роль | Датасет | Назначение | Source |
| --- | --- | --- | --- |
| `TRAIN` | ADFA IDS | Baseline HIDS training, normal/attack host traces, syscall sequences. | <https://research.unsw.edu.au/projects/adfa-ids-datasets>; <https://www.kaggle.com/datasets/alishamekhi/adfa-ids-datasets?resource=download> |
| `TRAIN` | LID-DS 2021 | Core sequence modelling dataset для Linux syscall behaviour. | <https://github.com/LID-DS/LID-DS> |
| `TRAIN` | Maintainable Log Dataset | Enterprise log behaviour и multi-stage attack modelling. | <https://data.niaid.nih.gov/resources?id=zenodo_5789063> |
| `VALIDATION` | LID-DS 2019 | Cross-version validation на CVE-based attack scenarios. | <https://github.com/LID-DS/LID-DS> |
| `VALIDATION` | LANL Dataset | User-host behaviour, authentication behaviour, lateral movement patterns. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| `VALIDATION` | Windows Event Log / OTRF Security Datasets | SOC-style validation на Windows/Sysmon telemetry. | <https://github.com/OTRF/Security-Datasets> |
| `TEST` | Unified Host + Network Dataset / LANL | Hybrid host+network validation, multi-source telemetry, feature-level fusion. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| `TEST` | ISOT Cloud IDS Dataset | Cloud environment validation, workloads, logs/syscalls/performance metrics. | <https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php> |
| `TEST` | Dynamic Malware Analysis Dataset | Malware-driven host behaviour и exfiltration-related activity. | <https://zenodo.org/record/1203289> |

###### Host dataset details

| Датасет | Роль | Что содержит | Почему нужен | Подходящие модели | Source |
| --- | --- | --- | --- | --- | --- |
| ADFA IDS | `TRAIN` | Linux/Windows system calls, normal traces, attack traces. | Стандартный HIDS baseline и сравнимость с research. | RF, XGBoost, LSTM, CNN. | <https://research.unsw.edu.au/projects/adfa-ids-datasets>; <https://www.kaggle.com/datasets/alishamekhi/adfa-ids-datasets?resource=download> |
| LID-DS 2021 | `TRAIN` | System calls, attack scenarios, normal behaviour, labelled traces. | Основной источник для LSTM/sequence branch. | LSTM, GRU, CNN-LSTM, Transformers. | <https://github.com/LID-DS/LID-DS> |
| Maintainable Log Dataset | `TRAIN` | Enterprise logs, 20 log types, multi-stage attacks via state machines. | Проверяет log-level multi-stage behaviour, а не только syscalls. | RF, XGBoost, LSTM/GRU, Autoencoder. | <https://data.niaid.nih.gov/resources?id=zenodo_5789063> |
| LID-DS 2019 | `VALIDATION` | CVE-based scenarios, syscall parameters, labelled attacks, benign traces. | Проверяет переносимость LID-DS 2021 -> 2019. | Same syscall/sequence models. | <https://github.com/LID-DS/LID-DS> |
| LANL Dataset | `VALIDATION` | Authentication logs, user-computer events, multi-day enterprise activity. | Закрывает user/auth/lateral movement поведение. | Graph/sequence/tabular auth models. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| Windows Event Log / OTRF | `VALIDATION` | Windows Event Logs, Sysmon, process/security events. | SOC-oriented validation и Windows telemetry. | RF, XGBoost, sequence/event models. | <https://github.com/OTRF/Security-Datasets> |
| Unified Host + Network / LANL | `TEST` | Host events, network events, authentication activity. | Финальная проверка hybrid host+network fusion. | Hybrid/late-fusion models. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| ISOT Cloud IDS | `TEST` | Cloud logs, syscalls, performance metrics. | Проверяет переносимость в cloud-like среду. | Resource/log/sequence models. | <https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php> |
| Dynamic Malware Analysis | `TEST` | Kernel calls, user-level activity, malware traces. | Проверяет malware-driven host behaviour. | API/syscall/process models. | <https://zenodo.org/record/1203289> |

###### Experiments only

| Датасет | Статус | Ограничение |
| --- | --- | --- |
| HDFS Log Dataset / LogHub | Experiments only | Не является security-focused dataset; использовать только для проверки log anomaly pipeline. |
| Synthetic syscall augmentation / extra syscall traces | Experiments only | Не использовать как основной источник ground truth без отдельной методологии. |

##### Attack lifecycle coverage

| Этап | Поддерживающие источники |
| --- | --- |
| Reconnaissance | OTRF, Maintainable Log Dataset, Unified Host-Network. |
| Privilege Escalation | OTRF, LANL, Unified Host-Network. |
| Lateral Movement | LANL, OTRF, Unified Host-Network. |
| Collection | ADFA IDS, LID-DS 2021/2019, Dynamic Malware Analysis, Maintainable Log Dataset, Unified Host-Network. |
| Data Staging | ADFA IDS, LID-DS 2021/2019, Maintainable Log Dataset, Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network. |
| Exfiltration | CIC-Bell-DNS-EXF-2021, CIC-Bell-DNS-2021, Mendeley DNS, Unified Host-Network. |

##### Minimal and optimal host stack

| Stack | Датасеты | Назначение |
| --- | --- | --- |
| Минимально достаточный | ADFA IDS; LID-DS 2021; Maintainable Log Dataset. | HIDS baseline, syscall sequence modelling, enterprise logs. |
| Оптимальный для proposal | ADFA IDS; LID-DS 2021; LID-DS 2019; LANL; Maintainable Log Dataset; Unified Host + Network / LANL. | Baseline + sequence + validation + user-host + enterprise + hybrid. |
| Расширенный | Windows Event Logs / OTRF; ISOT Cloud IDS; Dynamic Malware Analysis. | SOC telemetry, cloud portability, malware-driven behaviour. |

##### Stage Two implications

| Компонент Stage Two | Требование из dataset strategy |
| --- | --- |
| Catalog ingestion | Хранить dataset domain, role, source, format, checksum и source path. |
| Parser registry | DNS CSV/PCAP/TXT, host syscalls, logs, JSON/BSON, packet captures и netflow требуют разных parser classes. |
| Label resolver | Не считать unlabeled источники benign; filename/scenario labels только через explicit mapping. |
| Feature extraction | Использовать одинаковые функции признаков для roles, но сохранять role-separated artifacts. |
| Leakage checks | Исключать dataset name, role, scenario, path и label/source fields из model-ready X. |

##### Итоговое решение

Для proposal и дальнейшей реализации нужно поддерживать две независимые ветви:

```text
DNS branch:
  TRAIN -> CIC-Bell-DNS-EXF-2021 + CIC-Bell-DNS-2021
  VALIDATION -> split CIC-Bell-DNS-2021
  TEST -> Mendeley DNS Exfiltration Dataset

Host branch:
  TRAIN -> ADFA IDS + LID-DS 2021 + Maintainable Log Dataset
  VALIDATION -> LID-DS 2019 + LANL + Windows Event Logs / OTRF
  TEST -> Unified Host + Network / LANL + ISOT Cloud IDS + Dynamic Malware Analysis
```

Hybrid learning строится поверх feature-level fusion и late fusion. Raw logs, syscalls, packet captures и auth events не объединяются механически в один dataset.

---

### Источник: `docs/ru/feature_extraction_and_catalogue.md`

[Открыть исходный файл](ru/feature_extraction_and_catalogue.md)

#### Feature extraction map и каталог признаков

Документ объединяет `dataset_feature_extraction_map.md`, `feature_catalogue_full.md` и feature-related разделы `functional_project_cheatsheet.md`. Он задает контракт для Stage Two feature extraction, Parquet artifacts и model-ready datasets.

##### Назначение

Документ отвечает на два вопроса:

1. Из каких датасетов какие группы признаков извлекаются.
2. Какие признаки и поля должны существовать в feature artifacts без нарушения traceability и anti-leakage правил.

##### Принципы отбора признаков

1. `TRAIN`, `VALIDATION`, `TEST` не смешиваются.
2. DNS и Host не склеиваются на raw-level.
3. Labels не являются input features.
4. Leakage поля исключаются из model-ready `X`.
5. Sequence-признаки строятся отдельно от табличных aggregate features.
6. Отсутствие label не означает benign.
7. Timestamp ordering используется только при фактическом наличии timestamp или event order; текущее время не подставляется.

##### Уровни расчета

| Уровень | Описание | Модели |
| --- | --- | --- |
| Event-level | Один DNS query, syscall, process event, auth event, packet или log event. | RF, XGBoost, CNN |
| Window-level | Aggregates по host/source_ip/user/domain/process за окно. | RF, XGBoost, CNN |
| Flow-level | 5-tuple / сетевой flow. | RF, XGBoost |
| Trace-level | Syscall/API/module trace как последовательность. | CNN, LSTM |
| Sequence-level | Ordered multi-source events, плановый размер 50-100 событий. | LSTM |
| Hybrid-level | Корреляция host + network/DNS по времени, host, scenario или mapping. | Late fusion, RF/XGBoost, LSTM |

##### Dataset to feature map

| Датасет / источник | Роль | Основные группы признаков | Этапы атаки | Использование |
| --- | --- | --- | --- | --- |
| CIC-Bell-DNS-EXF-2021 | `TRAIN` | DNS lexical, entropy, RR/TTL, query-rate, inter-query intervals, unique subdomain ratio. | Exfiltration | Attack-class DNS source. |
| CIC-Bell-DNS-2021 | `TRAIN` + `VALIDATION` split | Те же DNS признаки, benign baseline, FP-control. | Exfiltration / benign baseline | Training normal DNS behaviour и threshold tuning. |
| Mendeley DNS Exfiltration | `TEST` | DNS lexical/temporal/numeric table, source IP windows. | Exfiltration | Финальная generalization check; не обучать. |
| ADFA IDS | `TRAIN` | Syscall frequencies, n-grams, transitions, trace length, collection syscalls. | Collection, Data Staging | HIDS/syscall benchmark. |
| LID-DS 2021 | `TRAIN` | Syscall/API sequence, syscall args, file access, inter-arrival timings. | Collection, Data Staging, Pre-exfiltration | Основной host sequence source. |
| LID-DS 2019 | `VALIDATION` | Те же syscall/sequence признаки, что LID-DS 2021. | Collection, Data Staging | Cross-version validation. |
| Maintainable Log Dataset | `TRAIN` | Log templates, event volume, multi-stage event sequences, file access/log correlation. | Reconnaissance, Collection, Data Staging | Enterprise log behaviour. |
| LANL Dataset | `VALIDATION` | Auth frequency, user-host interaction, failed login ratio, privileged account usage, lateral movement graph. | Privilege Escalation, Lateral Movement | Enterprise behaviour validation. |
| Windows Event Log / OTRF | `VALIDATION` | EventID, process tree, PowerShell/command line, logon/auth, object access, SourceAddress/DestAddress. | Reconnaissance, Privilege Escalation, Lateral Movement | SOC-oriented Windows/Sysmon validation. |
| Unified Host-Network / LANL | `TEST` | Host auth/process + netflow + correlation features. | Full lifecycle | Финальный hybrid test. |
| ISOT Cloud IDS | `TEST` | CPU/memory/I/O/log/cloud workload anomalies. | Data Staging | Cloud portability check. |
| Dynamic Malware Analysis | `TEST` | API/syscall events, command line/path/module tokens, process tree, sandbox lifecycle. | Collection, Data Staging, Pre-exfiltration | Malware-driven host behaviour check. |
| DNS VALIDATION pcap | `VALIDATION` | Amplification ratio, qname/qtype, response size, TTL, RCODE/NXDOMAIN, packet/byte counts. | DNS exfiltration/amplification | Requires DNS packet parser. |
| DNS VALIDATION txt | `VALIDATION` | Domain length, label count, TLD/SLD, entropy. | Domain validation | `unknown` не использовать как class без policy. |
| Host packet captures | `VALIDATION` / `TEST` | Packet/flow counts, protocol distribution, ports, TCP flags, DNS/LDAP/SMB/DCERPC indicators. | Reconnaissance, Lateral Movement, Exfiltration | Labels через scenario/external mapping. |
| Host TEST bson/json/txt | `TEST` | API/syscall-like frequencies, n-grams, transitions, args, process context, command/path entropy. | Collection, Data Staging | Evaluation only. |
| Host TEST csv | `TEST` | Flow duration, bytes/packets, ports, protocol, fan-in/fan-out, TCP flags. | Reconnaissance, Lateral Movement, Exfiltration | TEST-only; не обучать. |

##### DNS feature catalogue

| Группа | Примеры признаков | Формула / расчет | Stage Two parser dependency |
| --- | --- | --- | --- |
| Lexical | `dns_query_length`, `dns_subdomain_length`, `dns_subdomain_depth`, `dns_label_count`, `dns_label_avg_len`, `dns_label_max_len`, `dns_digit_count`, `dns_special_char_count`. | String parsing по qname/FQDN/subdomain. | DNS CSV/TXT/PCAP parser. |
| Entropy | `dns_entropy`, `dns_rr_name_entropy`, `url_token_entropy`. | Shannon entropy по domain/query/url tokens. | DNS parser + URL/domain tokenizer. |
| N-grams | `dns_1gram_frequency`, `dns_2gram_frequency`, `dns_3gram_frequency`. | Character/token n-gram counts. | Domain tokenizer. |
| Categorical/enrichment | `dns_tld`, `dns_sld`, `domain_age_days`, `name_server_count`, `unique_asn_count`, `unique_country_count`. | Extract/enrich and encode safely. | DNS parser + optional enrichment. |
| RR/protocol | `ttl_mean`, `ttl_variance`, `unique_ttl_count`, `rr_count`, `rr_rate`, `rr_type_frequency_*`, `dns_qtype_frequency`, `dns_rcode_distribution`, `dns_nxdomain_rate`. | Aggregates по RR/query/response/window. | DNS packet/pcap.csv parser. |
| Temporal | `dns_inter_query_interval_stats`, `dns_query_rate`, `dns_queries_per_window`. | `diff(timestamp)` and count over sliding window. | Timestamp-aware DNS events. |
| Network/DNS bridge | `dns_response_size_stats`, `dns_amplification_ratio`, `dns_source_ip_query_count`, `dnsbl_provider_match`. | Packet/response/window aggregates. | DNS packet parser + source IP fields. |

##### Network / flow / packet feature catalogue

| Группа | Примеры признаков | Расчет |
| --- | --- | --- |
| Volume | `packet_count`, `byte_count`, `flow_duration`, `packet_size_mean`, `packet_size_std`. | Group by flow/window. |
| Timing | `inter_arrival_time_stats`. | `diff(timestamp)` by flow/src/dst. |
| Protocol/ports | `protocol_distribution`, `src_port_frequency`, `dst_port_frequency`, TCP flag counts. | Counts/ratios over window. |
| Directionality | `outbound_byte_ratio`, `external_destination_count`, fan-in/fan-out, unique dst hosts. | Internal/external mapping + flow aggregates. |

##### Host feature catalogue

| Группа | Примеры признаков | Источники |
| --- | --- | --- |
| Syscall/API sequence | `syscall_frequency`, `syscall_ngram_2_frequency`, `syscall_ngram_3_frequency`, `syscall_transition_probability`, `unique_syscall_count`, `syscall_trace_length`, `syscall_interarrival_stats`. | ADFA, LID-DS, Host txt/sc/ghc/bson/json. |
| Collection indicators | `collection_syscall_count`, `directory_enumeration_count`, `file_access_count`, `file_access_rate`, `file_access_entropy`, `unique_file_count`, `sensitive_file_extension_count`. | Syscalls, logs, Windows object access, malware traces. |
| API/sandbox/trace | `api_descriptor_frequency`, `api_category_frequency`, `api_arg_token_count`, `trace_module_frequency`, `trace_module_transition_frequency`, `trace_offset_distribution`, `trace_density`. | Dynamic Malware, Host BSON/JSON/GHC. |
| Authentication | `login_success_count`, `login_failure_count`, `failed_login_ratio`, `failed_then_success_login_indicator`, `session_opened_count`, `session_duration_stats`, `sudo_activity_count`, `sshd_activity_count`. | LANL, OTRF, auth logs, wls_day. |
| User/host graph | `user_host_interaction_count`, `source_ip_auth_frequency`, `auth_baseline_deviation`, `source_loghost_graph_degree`. | LANL, Windows logs, wls_day. |
| Windows/Sysmon/process | `event_id_frequency`, `security_event_sequence_entropy`, `logon_type_distribution`, `parent_child_process_count`, `process_name_frequency`, `command_line_length`, `command_line_entropy`, `encoded_powershell_indicator`, `rare_process_execution_score`. | OTRF, Windows Event Logs, Dynamic Malware. |
| Filesystem/resource telemetry | `filesystem_used_pct_stats`, `filesystem_pressure_ratio`, `inode_free_ratio`, `disk_read_bytes_rate`, `disk_write_bytes_rate`, `cpu_total_pct_stats`, `memory_usage_stats`, `load_average_stats`. | Host metric logs, ISOT Cloud IDS. |
| Network/resource bridge | `network_interface_bytes_rate`, `socket_count`, `source_dest_address_port_count`. | Host network telemetry, Windows events, netflow. |
| Logs/templates | `log_event_count`, `log_volume_rate`, `log_level_frequency`, `warning_error_count`, `component_frequency`, `message_template_frequency`, `event_type_frequency`, `alert_count`. | Maintainable logs, syslog/messages/mainlog, sandbox logs. |
| Staging/compression | `archive_creation_count`, `compression_process_indicator`, `process_path_entropy`, `suspicious_path_indicator`, `module_path_entropy`. | Windows/process logs, malware, command-line telemetry. |

##### Hybrid and sequence catalogue

| Признак | Назначение |
| --- | --- |
| `host_network_time_delta` | Временной лаг между nearest host event и network event. |
| `process_to_network_burst_score` | Связь запуска процесса и последующего network burst. |
| `auth_to_network_correlation` | Количество network flows после auth event/window. |
| `file_to_network_correlation` | Связь file access/data staging с network outflow. |
| `cpu_io_network_correlation` | Rolling correlation CPU/disk/network spikes. |
| `cross_source_event_count` | Количество событий из разных sources в одном unified window. |
| `sequence_window_event_count` | Количество events в LSTM window. |
| `sequence_window_duration` | Длительность sequence window. |
| `sequence_event_type_entropy` | Entropy over ordered event type tokens. |
| `sequence_temporal_order_pattern` | Ordered stage/event tokens. |
| `process_file_network_sequence` | Pattern: file access -> archive/compress -> outbound network event. |
| `stage_transition_pattern` | Переходы Reconnaissance -> Privilege Escalation -> Lateral Movement -> Collection -> Data Staging -> Exfiltration. |

##### Минимальный feature schema для Parquet artifacts

###### Traceability fields

| Поле | Назначение | Использовать как model feature |
| --- | --- | --- |
| `event_id` | ID normalized event. | Нет |
| `source_file_id` | ID raw-файла из catalog. | Нет |
| `source_row_id` / `packet_id` | Row/packet/event index. | Нет |
| `dataset_domain` | `dns`, `host`, `network`, `hybrid`. | Нет |
| `dataset_role` | `TRAIN`, `VALIDATION`, `TEST`. | Нет |
| `dataset_name` | Dataset name. | Нет, кроме audit/reporting |
| `dataset_format` | csv, pcap, json, log, bson, txt, etc. | Нет, кроме parser/debug |
| `parser_name` / `parser_version` | Parser traceability. | Нет |
| `event_timestamp` | Normalized event time. | Только derived time features / ordering |
| `window_id` | Window ID. | Нет |
| `sequence_id` | Sequence-window ID. | Нет |

###### Label fields

| Поле | Назначение |
| --- | --- |
| `label_binary` | 0=benign, 1=attack/exfiltration/malicious, NULL=unknown. |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, collection, data_staging, unknown. |
| `label_subtype` | Specific subtype/scenario, если доступен. |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none. |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label. |
| `label_confidence` | 1.0 explicit; 0.7-0.9 inferred; 0.4-0.7 weak; 0 unlabeled. |
| `label_mapping_rule_id` | ID label resolver rule. |

##### Что исключать из model-ready X

| Поле / группа | Почему исключать |
| --- | --- |
| `source_file`, basename, full path | Может кодировать `benign`, `malware`, `attack`, `exfiltration`. |
| `dataset_role` | TRAIN/VALIDATION/TEST leakage. |
| `dataset_name` | Модель может запомнить dataset вместо поведения. |
| `scenario_name`, `image_name` | Использовать только для label join/evaluation metadata. |
| `label_*` | Target/audit fields, не input features. |
| Raw payload/body | Проект ориентирован на metadata/behavioural detection, не payload inspection. |
| Абсолютные локальные пути | Непереносимы и создают leakage risk. |

##### Приоритет реализации

| Priority | Feature groups |
| --- | --- |
| P0 | DNS lexical/entropy/temporal/protocol; host syscall/API; auth; Windows/Sysmon; network volume/ports; sequence window basics; stage transition patterns. |
| P1 | Domain enrichment; hybrid correlations; resource telemetry; archive/compression; sensitive file access; graph/baseline features. |
| P2 | Advanced command-line tokenization; template mining; long-term per-user/per-host baselines; feature stability checks. |

##### Рекомендуемый порядок реализации в коде

1. Сформировать machine-readable `feature_catalog.yml/json` из этого документа.
2. Проверить, что parser outputs соответствуют normalized event schema.
3. Реализовать extractors по группам:
   - `dns_lexical_extractor`
   - `dns_protocol_extractor`
   - `dns_temporal_extractor`
   - `network_flow_extractor`
   - `host_syscall_extractor`
   - `host_auth_extractor`
   - `windows_event_extractor`
   - `resource_telemetry_extractor`
   - `hybrid_correlation_extractor`
   - `sequence_window_builder`
4. Сохранять результаты в Parquet layers:
   - `normalized_events/`
   - `feature_windows/`
   - `sequence_windows/`
   - `model_ready/`
5. Для каждого output сохранять `feature_extraction_report.md`: rows, missing values, label coverage, leakage checks.

##### Связь со Stage Two

| Stage Two layer | Требование |
| --- | --- |
| Parser pipeline | Каждый feature group зависит от конкретного parser output и normalized schema. |
| PostgreSQL Catalog | Хранит metadata, paths, statuses, hashes, reports, но не большие feature tables. |
| Parquet artifacts | Хранят normalized events, feature windows, sequence windows, model-ready X/y. |
| DuckDB checks | Проверяют Parquet counts, schema drift, split contamination, leakage columns. |
| LabelResolver | Заполняет label fields отдельно от X features. |
| Traceability | Feature/model-ready artifacts должны вести к normalized -> parser run -> raw dataset file. |

---

## Анализ датасетов

### Источник: `docs/ru/analysis-dataset/README.md`

[Открыть исходный файл](ru/analysis-dataset/README.md)

#### Анализ датасетов

Раздел фиксирует результаты Stage One анализа DNS/Host датасетов и переводит их в удобную форму для Stage Two normalization, parser registry и feature extraction.

##### Что изменено в структуре

Старые per-format отчеты были полезны как сырые заметки, но создавали дубли:

- `dns/<role>/<format>.md` и `host/<role>/<format>.md` повторяли одну и ту же структуру для 64 format buckets;
- `general_dns_*` и `general_host_*` агрегировали те же сведения повторно;
- `analysis-dataset.md` и `dataset_labels_availability_and_recommendations.md` частично пересекались с normalization/label docs.

Новая структура оставляет данные по counts/status/labels/timestamps/readiness в тематических документах:

| Документ | Назначение |
| --- | --- |
| [dns_datasets.md](ru/analysis-dataset/dns_datasets.md) | DNS TRAIN/VALIDATION/TEST: форматы, количество файлов, labels, timestamp/readiness, parser notes. |
| [host_datasets.md](ru/analysis-dataset/host_datasets.md) | Host TRAIN/VALIDATION/TEST: семейства данных, количество файлов, quality risks, parser notes. |
| [format_status_matrix.md](ru/analysis-dataset/format_status_matrix.md) | Единая таблица 64 format buckets со статусом readiness и ключевыми фактами. |
| [labels_and_readiness.md](ru/analysis-dataset/labels_and_readiness.md) | Label availability, canonical label rules, readiness statuses и anti-leakage правила. |
| [parser_feature_recommendations.md](ru/analysis-dataset/parser_feature_recommendations.md) | Рекомендации для Stage Two parser implementations и feature extraction. |
| [source_inventory.md](ru/analysis-dataset/source_inventory.md) | Индекс старых файлов, которые были объединены в новую структуру. |

Связанные документы:

- [../normalization/README.md](ru/normalization/README.md)
- [../normalization/parser_strategy.md](ru/normalization/parser_strategy.md)
- [../normalization/label_resolver.md](ru/normalization/label_resolver.md)
- [../normalization/normalized_event_schema.md](ru/normalization/normalized_event_schema.md)
- [../feature_extraction_and_catalogue.md](ru/feature_extraction_and_catalogue.md)
- [../dataset_strategy_dns_host.md](ru/dataset_strategy_dns_host.md)

##### Покрытие анализа

| Группа | Format buckets | Файлов | Основной смысл |
| --- | ---: | ---: | --- |
| `dns/TRAIN` | 3 | 26 | DNS train: CSV, PCAP и `pcap.csv`. |
| `dns/VALIDATION` | 2 | 8 | DNS validation: PCAP и domain-list TXT. |
| `dns/TEST` | 3 | 1 | DNS test: фактически доступен только CSV. |
| `host/TRAIN` | 43 | 60365 | Host train: telemetry, logs, JSON/JSON-lines, traces, flows, pcap. |
| `host/VALIDATION` | 8 | 6686 | Host validation: metadata, JSON-lines, flows, traces, packet captures. |
| `host/TEST` | 5 | 294584 | Host test: BSON, CSV, JSON, logs, traces. |
| **Итого** | **64** | **361670** | DNS и Host источники для feature extraction. |

##### Статусы готовности

| Статус | Format buckets | Файлов | Значение |
| --- | ---: | ---: | --- |
| `READY_FOR_FEATURE_EXTRACTION` | 42 | 288866 | Формат можно подключать к feature extraction после streaming/schema-aware normalization. |
| `NEEDS_CUSTOM_PARSER` | 14 | 72666 | Нужен специализированный parser или decoder. |
| `PARTIALLY_SUPPORTED` | 6 | 138 | Формат частично пригоден, но содержит под-схемы, служебные файлы или требует fixed schema. |
| `BROKEN_OR_EMPTY` | 2 | 0 | В подготовленном bucket нет входных файлов. |

##### Инварианты использования

1. `TRAIN`, `VALIDATION` и `TEST` не смешиваются.
2. `TEST` не используется для обучения, fit preprocessing, feature selection или threshold tuning.
3. Отсутствие label не означает benign.
4. Filename/class hints являются label source только при явном mapping и audit trail.
5. Raw files не изменяются; Stage Two должен сохранять traceability.
6. Для отсутствующего timestamp нельзя синтетически подставлять текущее время.

##### Сводный pipeline

```mermaid
flowchart TD
    A["Stage One analyze/sort/save-sort"] --> B["analysis-dataset docs"]
    B --> C["format_status_matrix.md"]
    B --> D["labels_and_readiness.md"]
    B --> E["parser_feature_recommendations.md"]
    C --> F["Stage Two parser registry"]
    D --> G["LabelResolver and quality checks"]
    E --> H["Normalization and feature extraction"]
```

##### Практический вывод

DNS-часть компактная и в основном требует DNS packet parser для PCAP/PCAPNG и fixed schema для DNS TEST CSV. Host-часть крупная и неоднородная: основная ценность для ML находится в telemetry/log/trace данных, но pipeline должен быть format-aware, streaming-friendly и label-safe.

---

### Источник: `docs/ru/analysis-dataset/source_inventory.md`

[Открыть исходный файл](ru/analysis-dataset/source_inventory.md)

#### Индекс объединенных источников

Документ фиксирует, какие старые файлы были объединены в новую тематическую структуру. Он нужен, чтобы не потерять навигацию после удаления дублей.

##### Новые документы

| Новый документ | Что содержит |
| --- | --- |
| [README.md](ru/analysis-dataset/README.md) | Общая карта раздела, coverage, readiness counts, инварианты. |
| [dns_datasets.md](ru/analysis-dataset/dns_datasets.md) | Все DNS TRAIN/VALIDATION/TEST сведения. |
| [host_datasets.md](ru/analysis-dataset/host_datasets.md) | Все Host TRAIN/VALIDATION/TEST сведения. |
| [format_status_matrix.md](ru/analysis-dataset/format_status_matrix.md) | 64 format buckets: files/status/labels/timestamp/action. |
| [labels_and_readiness.md](ru/analysis-dataset/labels_and_readiness.md) | Label policy, readiness statuses, LabelResolver guidance. |
| [parser_feature_recommendations.md](ru/analysis-dataset/parser_feature_recommendations.md) | Parser priorities, feature groups, quality checks. |

##### Старые верхнеуровневые файлы

| Старый файл | Куда перенесено содержание |
| --- | --- |
| `analysis-dataset.md` | `README.md`, `dns_datasets.md`, `host_datasets.md`, `parser_feature_recommendations.md`. |
| `dataset_labels_availability_and_recommendations.md` | `labels_and_readiness.md`, `parser_feature_recommendations.md`. |

##### Старые агрегаты по split

| Старый файл | Куда перенесено содержание |
| --- | --- |
| `dns/train/general_dns_train.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/validation/general_dns_validation.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/test/general_dns_test.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `host/train/general_host_train.md` | `host_datasets.md`, `format_status_matrix.md`, `parser_feature_recommendations.md`. |
| `host/validation/general_host_validation.md` | `host_datasets.md`, `format_status_matrix.md`. |
| `host/test/general_host_test.md` | `host_datasets.md`, `format_status_matrix.md`. |

##### Старые per-format файлы

###### DNS

| Старый каталог | Файлы | Новый документ |
| --- | --- | --- |
| `dns/train/` | `csv.md`, `pcap.md`, `pcap.csv.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/validation/` | `pcap.md`, `txt.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/test/` | `csv.md`, `pcap.md`, `pcap.csv.md` | `dns_datasets.md`, `format_status_matrix.md`. |

###### Host TRAIN

`host/train/*.md` был объединен в `host_datasets.md` и `format_status_matrix.md`.

Список форматов: `auth.log`, `cpu.log`, `csv`, `diskio.log`, `filesystem.log`, `fsstat.log`, `ghc`, `info`, `journal`, `journal~`, `json`, `json-1`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `netflow_ids`, `network.log`, `pcap`, `process.log`, `process.summary.log`, `sc`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `txt`, `uptime.log`, `xml`.

###### Host VALIDATION

`host/validation/*.md` был объединен в `host_datasets.md` и `format_status_matrix.md`.

Список форматов: `cap`, `csv`, `json`, `netflow_day`, `pcap`, `pcapng`, `txt`, `wls_day`.

###### Host TEST

`host/test/*.md` был объединен в `host_datasets.md` и `format_status_matrix.md`.

Список форматов: `bson`, `csv`, `json`, `log`, `txt`.

##### Почему старые файлы удаляются

Старые документы содержали полезные исходные observations, но:

- дублировали структуру и выводы в `general_*`;
- усложняли навигацию по 80 файлам;
- мешали видеть общую readiness/label картину;
- часть сведений была уже отражена в normalization/code documentation.

Ключевые данные из них перенесены в новую тематическую структуру.

---

### Источник: `docs/ru/analysis-dataset/dns_datasets.md`

[Открыть исходный файл](ru/analysis-dataset/dns_datasets.md)

#### DNS datasets

DNS-ветка содержит 8 format buckets и 35 файлов. Она делится на табличные CSV, packet captures и domain-list TXT. DNS `TEST` не содержит подготовленных `pcap`/`pcap.csv` файлов, поэтому TEST packet-level проверка в текущем наборе невозможна.

##### DNS TRAIN

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `csv` | 8 | `PARTIALLY_SUPPORTED` | class hint из имени файла: `benign`, `malware`, `phishing`, `spam` | частично | Domain-list и PhishTank-like файлы читаются напрямую; feature CSV могут содержать неэкранированные list/dict поля с запятыми. |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | class hint из имени файла: `benign`, `malware`, `phishing`, `spam` | да, packet timestamp | Нужен packet parser с classic pcap/pcapng и DNS protocol decoding. |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | class hint из имени файла: `audio`, `benign`, `compressed`, `exe`, `image`, `text`, `video` | да | CSV-структура стабильна, заголовки присутствуют; подходит для DNS feature extraction после label mapping. |

Правило labels: filename/class hint можно использовать только как `label_source=filename`/`inferred_label`. Payload classes (`audio`, `compressed`, `exe`, `image`, `text`, `video`) нельзя автоматически считать exfiltration labels без зафиксированного target mapping.

##### DNS VALIDATION

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | class hint из имени файла: `attack`, `benign` | да, packet timestamp | Подходит для проверки DNS amplification/detection pipeline, но требует packet parser. |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | class hint: `unknown`, `benign` | нет | Domain-list: одна доменная запись на строку. `unknown` нельзя считать benign или attack без policy. |

##### DNS TEST

| Формат | Файлов | Статус | Labels | Timestamp | Назначение и ограничения |
| --- | ---: | --- | --- | --- | --- |
| `csv` | 1 | `PARTIALLY_SUPPORTED` | частичное boolean-like поле `label_or_flag` в sample | да | Большой CSV без заголовка; нужна закрепленная 22-колоночная схема и streaming-read. Использовать только для evaluation. |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | нет | нет | В подготовленном `TEST.pcap` нет файлов. |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | нет | нет | В подготовленном `TEST.pcap.csv` нет файлов. |

##### Выводы для DNS parsers

| Компонент Stage Two | Что требуется |
| --- | --- |
| `DnsCsvParser` | Различать TRAIN CSV под-схемы, DNS TEST headerless 22-column schema и domain-list/PhishTank-like sources. |
| `DnsPcapCsvParser` | Поддерживать стабильные CSV headers и сохранять filename class hints как label metadata. |
| `DnsTxtDomainListParser` | Читать одну доменную запись на строку, сохранять `timestamp=null`, `timestamp_type=missing` или `event_order`. |
| `DnsPacketCaptureParser` | Извлекать packet timestamp, DNS query/response fields, qtype/qclass/rcode/ttl, network tuple и packet-level metadata. |

##### DNS feature extraction

Приоритетные признаки:

- длина домена, поддомена, query string;
- entropy и charset distribution;
- unique subdomain ratio;
- query rate/window counts;
- qtype/rcode/ttl distribution;
- packet size/response size;
- payload class context для pcap.csv, если mapping утвержден.

##### DNS quality risks

- DNS TEST packet buckets пустые (`BROKEN_OR_EMPTY`).
- DNS TEST CSV без header требует fixed positional schema.
- `unknown` в VALIDATION TXT не является class label.
- Filename labels требуют audit trail и не должны попадать в X features.

---

### Источник: `docs/ru/analysis-dataset/host_datasets.md`

[Открыть исходный файл](ru/analysis-dataset/host_datasets.md)

#### Host datasets

Host-ветка содержит 56 format buckets и 361635 файлов. Это основной источник host telemetry, sequence traces, runtime logs, Windows/Sysmon-like событий, network flows и packet captures.

##### Host TRAIN

Host TRAIN содержит 43 format buckets и 60365 файлов. Это основной источник для обучения, но не все форматы имеют labels и не все пригодны для универсального reader.

###### Сводка по семействам

| Семейство | Форматы | Статус обработки |
| --- | --- | --- |
| Metrics/telemetry | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | Большинство готовы к feature extraction; `cpu.log` и `diskio.log` частично поддержаны из-за под-схем. |
| Logs | `auth.log`, `info`, `journal`, `journal~`, `log*`, `syslog*`, `messages*`, `mainlog*`, `mail-*` | Требуют schema-aware routing; `journal`/`journal~` требуют отдельный toolchain. |
| Structured/semi-structured | `csv`, `json`, `json-1`, `xml` | CSV частично поддержан из-за служебных файлов; JSON требует schema-aware parser. |
| Network/hybrid | `netflow_ids`, `pcap` | `netflow_ids` готов; `pcap` требует packet/parser layer. |
| Behaviour traces | `ghc`, `sc`, `txt` | `ghc` требует custom parser; `sc`/`txt` пригодны для sequence features. |

###### Ключевые Host TRAIN форматы

| Формат | Файлов | Статус | Важные факты |
| --- | ---: | --- | --- |
| `csv` | 101 | `PARTIALLY_SUPPORTED` | Есть telemetry CSV и служебные `feature_descr.csv`/`ground_truth.csv`; labels в колонках 7/8/9 и binary label 0/1. |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | Есть metric rows и annotation rows с labels `crack_passwords`, `escalate`; нужен parser split. |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | Минимум две под-схемы: `system.diskio` и `host.disk.*`. |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | Смешение raw syslog и JSON-lines. |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | Очень большой trace corpus; sample показывает 200 tokens на файл. |
| `journal`, `journal~` | 18 | `NEEDS_CUSTOM_PARSER` | Binary/systemd journal; нельзя читать как обычный text log. |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | Смешанные схемы, scenario docs, `exploit`, `container.role`, `alert`. |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | Требует packet parser. |
| `filesystem.log`, `fsstat.log` | 24 | `READY_FOR_FEATURE_EXTRACTION` | JSON-lines storage telemetry. |
| `sc`, `txt` | 3380 | `READY_FOR_FEATURE_EXTRACTION` | Syscall/API sequence traces; нужны streaming и sequence-aware features. |

##### Host VALIDATION

Host VALIDATION содержит 8 format buckets и 6686 файлов.

| Формат | Файлов | Статус | Labels | Timestamp | Назначение |
| --- | ---: | --- | --- | --- | --- |
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | packet timestamp | Network/hybrid validation; нужен pcap/cap parser. |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `is_executing_exploit`: False 5813, True 187 | частично | Validation metadata и labels/context. |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | JSON Lines Windows/Sysmon telemetry. |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Большие line-oriented network flows. |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | packet timestamp | Packet validation. |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | packet timestamp | Packet validation, pcapng parser. |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Line-oriented syscall traces. |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Windows/Sysmon-like events. |

Validation packet/flow/traces без встроенных labels нужно связывать с validation CSV по `scenario_name`, `image_name`, filename, recording time, exploit start time и timestamp windows.

##### Host TEST

Host TEST содержит 5 format buckets и 294584 файлов. Набор нельзя использовать для обучения, но он важен для inference/evaluation.

| Формат | Файлов | Статус | Labels | Timestamp | Назначение |
| --- | ---: | --- | --- | --- | --- |
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | нет | частично через порядок/`t`/`h` | Sandbox behaviour sequence; нужен BSON parser и сопоставление descriptor/event docs по `I`. |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | label в отдельных label CSV | да | Network/hybrid evaluation; labels join по IP или подтвержденному ключу. |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | нет | да | JSON Lines, Mongo-style `NumberLong(...)`, большие reports. |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Line-oriented sandbox runtime logs. |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Syscall/API sequence traces; очень большое число файлов. |

##### Host feature extraction

Приоритетные признаки:

- process/service/socket counts and transitions;
- syscall/API n-grams and sequence embeddings;
- authentication success/failure and session patterns;
- filesystem, CPU, memory, disk I/O, network telemetry aggregates;
- flow statistics, packet protocol distributions;
- Windows/Sysmon event IDs, parent-child process chains;
- alert/context fields as metadata, not X labels.

##### Host quality risks

- Mixed schemas inside one extension: especially `json`, `log`, `syslog*`, `txt`, `xml`, `pcap` in TRAIN.
- Очень большие источники: TEST `txt`, `bson`, `json`, `log`.
- Missing embedded labels in most Host telemetry/log/packet/sequence files.
- Packet formats require binary parsers; BSON and Mongo-style JSON require specialized decoders.

---

### Источник: `docs/ru/analysis-dataset/format_status_matrix.md`

[Открыть исходный файл](ru/analysis-dataset/format_status_matrix.md)

#### Матрица форматов и статусов

Матрица сохраняет ключевые данные из 66 старых per-format отчетов: split, format, число файлов, readiness, label availability, timestamp availability и основное ограничение. Полные старые пути перечислены в [source_inventory.md](ru/analysis-dataset/source_inventory.md).

##### Сводка по статусам

| Статус | Format buckets | Файлов |
| --- | ---: | ---: |
| `READY_FOR_FEATURE_EXTRACTION` | 42 | 288866 |
| `NEEDS_CUSTOM_PARSER` | 14 | 72666 |
| `PARTIALLY_SUPPORTED` | 6 | 138 |
| `BROKEN_OR_EMPTY` | 2 | 0 |

##### DNS

| Role | Формат | Файлов | Статус | Labels | Timestamp | Ограничение / действие |
| --- | --- | ---: | --- | --- | --- | --- |
| `TRAIN` | `csv` | 8 | `PARTIALLY_SUPPORTED` | class hints: benign/malware/phishing/spam | частично | Нужна schema-aware normalization для feature CSV с list/dict полями. |
| `TRAIN` | `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | filename class hints | да | Нужен packet parser с DNS decoding. |
| `TRAIN` | `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | filename class hints: audio/benign/compressed/exe/image/text/video | да | Готов к DNS feature extraction после label mapping. |
| `VALIDATION` | `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | filename class hints: attack/benign | да | Нужен packet parser для validation packet features. |
| `VALIDATION` | `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | filename hints: unknown/benign | нет | Domain-list; `unknown` требует отдельной policy. |
| `TEST` | `csv` | 1 | `PARTIALLY_SUPPORTED` | partial boolean-like `label_or_flag` | да | Headerless 22-column schema; только evaluation. |
| `TEST` | `pcap` | 0 | `BROKEN_OR_EMPTY` | нет | нет | Bucket пустой. |
| `TEST` | `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | нет | нет | Bucket пустой. |

##### Host TRAIN

| Формат | Файлов | Статус | Labels | Timestamp | Ограничение / действие |
| --- | ---: | --- | --- | --- | --- |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | нет | да | Raw syslog + JSON-lines; нужен parser с ветвлением. |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | embedded/annotation labels: crack_passwords, escalate | да | Разделить metric rows и annotation rows. |
| `csv` | 101 | `PARTIALLY_SUPPORTED` | attack categories + binary 0/1 | да | Отличать telemetry CSV от `feature_descr.csv` и `ground_truth.csv`. |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | нет | да | Минимум две под-схемы: `system.diskio` и `host.disk.*`. |
| `filesystem.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | JSON-lines storage telemetry. |
| `fsstat.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | JSON-lines storage telemetry. |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | нет | нет | Специализированный trace parser; большой объем. |
| `info` | 3 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Mail/service logs; schema-aware parser. |
| `journal` | 17 | `NEEDS_CUSTOM_PARSER` | нет | нет | Binary/systemd journal. |
| `journal~` | 1 | `NEEDS_CUSTOM_PARSER` | нет | нет | Binary/systemd journal backup. |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | schema-dependent: exploit/container.role/alert | да | Смешанные schemas; нужен schema-aware parser. |
| `json-1` | 1 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware extraction; labels только через resolver. |
| `load.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | нет | нет/контекстно | Telemetry; timestamp может быть вложенным/контекстным. |
| `log` | 98 | `NEEDS_CUSTOM_PARSER` | context hints | да | Mixed JSON/scenario/log schemas. |
| `log-1` | 32 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `log-2` | 9 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Schema-aware parser layer. |
| `log-3` | 8 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Schema-aware parser layer. |
| `mail-info-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Mail log parser. |
| `mail-warn-1` | 2 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Mail log parser. |
| `mainlog` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `mainlog-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `mainlog-2` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `mainlog-3` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Schema-aware parser layer. |
| `memory.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Metric telemetry; labels external only. |
| `messages` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `messages-1` | 3 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `netflow_ids` | 50 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Flow-like source; line-oriented parser. |
| `network.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Network telemetry. |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | нет | нет в extracted summary | Требуется packet parser. |
| `process.log` | 2 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Process event features. |
| `process.summary.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Process summary features. |
| `sc` | 210 | `READY_FOR_FEATURE_EXTRACTION` | context hints | да | Syscall/API trace parser. |
| `service.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Service telemetry. |
| `socket.summary.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Socket summary features. |
| `syslog` | 9 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog-1` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog-2` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog-3` | 10 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog-4` | 1 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `syslog.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Syslog-like parser. |
| `txt` | 3170 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Sequence/trace parser; streaming required. |
| `uptime.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | Uptime/metric features. |
| `xml` | 40 | `READY_FOR_FEATURE_EXTRACTION` | context hints | нет | XML/schema-aware parser. |

##### Host VALIDATION

| Формат | Файлов | Статус | Labels | Timestamp | Ограничение / действие |
| --- | ---: | --- | --- | --- | --- |
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | да | Packet parser; labels через scenario/CSV join. |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `is_executing_exploit`: False 5813, True 187 | частично | Validation labels/context. |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Windows/Sysmon JSON Lines. |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Большие flow files; external labels only. |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | да | Packet parser; labels через scenario/CSV join. |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | нет внутри файла | да | PCAPNG parser. |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Syscall traces; streaming required. |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Windows/Sysmon-like events. |

##### Host TEST

| Формат | Файлов | Статус | Labels | Timestamp | Ограничение / действие |
| --- | ---: | --- | --- | --- | --- |
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | нет | частично | BSON parser; descriptor/event join по `I`. |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | external label CSV | да | Labels только для evaluation; join по IP/ключу. |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | нет | да | JSON Lines, Mongo-style `NumberLong(...)`, reports. |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Sandbox runtime logs. |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | нет | да | Очень большие syscall/API traces; нужен streaming. |

---

### Источник: `docs/ru/analysis-dataset/labels_and_readiness.md`

[Открыть исходный файл](ru/analysis-dataset/labels_and_readiness.md)

#### Labels и readiness

Документ объединяет сведения о label availability и parser/feature readiness из старого `dataset_labels_availability_and_recommendations.md` и per-format отчетов.

##### Главные правила

1. Отсутствие label не означает benign.
2. `TEST` нельзя использовать для обучения, fit preprocessing, feature selection или threshold tuning.
3. Labels из filename, directory, scenario metadata или IDS alert должны иметь `label_source`, `label_status`, confidence и traceability.
4. Weak labels не равны ground truth.
5. Для файлов без labels сохранять `label_binary = null`, `label_source = none`, `label_status = unlabeled`.
6. Label/source fields не должны попадать в model-ready `X`.

##### Canonical label fields

| Поле | Назначение |
| --- | --- |
| `label_binary` | `0=benign`, `1=malicious/attack/exfiltration`, `null=unknown`. |
| `label_family` | benign, dns_exfiltration, malware, phishing, lateral_movement, privilege_escalation, unknown. |
| `label_subtype` | subtype/scenario, если доступен. |
| `label_source` | embedded_column, filename, scenario_metadata, external_label_file, ids_alert, ground_truth_csv, none. |
| `label_status` | explicit_label, inferred_label, weak_label, partial_label, unlabeled, conflicting_label. |
| `label_confidence` | 1.0 для explicit, ниже для inferred/weak, null/0 для unlabeled. |
| `label_mapping_rule_id` | ID правила mapping. |
| `dataset_role` | TRAIN / VALIDATION / TEST. |
| `source_file` | Исходный путь/имя файла. |
| `source_event_id` | Строка/пакет/событие, если применимо. |

##### Label availability summary

| Категория | Format buckets | Источники |
| --- | ---: | --- |
| Прямые labels | 5 | Host TRAIN `cpu.log`, Host TRAIN `csv`, Host TRAIN `json`, Host VALIDATION `csv`, Host TEST `csv` через label CSV. |
| Частичные labels / class hints | 6 | DNS TRAIN `csv`/`pcap`/`pcap.csv`, DNS VALIDATION `pcap`/`txt`, DNS TEST `csv`. |
| Без встроенных labels | 55 | Большинство host telemetry/log/packet/sequence formats. |

##### Источники с прямыми labels

| Domain | Role | Формат | Файлов | Label field/source | Values | Как использовать |
| --- | --- | ---: | ---: | --- | --- | --- |
| Host | `TRAIN` | `cpu.log` | 13 | `labels` annotation rows | `crack_passwords`, `escalate` | Partial/weak labels; связать с metric windows по timestamp/host. |
| Host | `TRAIN` | `csv` | 101 | columns 7/8/9 | normal/attack categories + binary 0/1 | Основной supervised TRAIN источник после schema-aware normalization. |
| Host | `TRAIN` | `json` | 219 | `exploit` / `container.role` / `alert` | True/False/normal/victim/alert-derived | Schema-dependent; `exploit` inferred, `alert` weak, `container.role` context. |
| Host | `VALIDATION` | `csv` | 6 | `is_executing_exploit` | False 5813, True 187 | Основной validation label/context источник. |
| Host | `TEST` | `csv` | 3 | external label CSV | scan/attack labels | Только final evaluation; не training. |

##### Источники с filename/class hints

| Domain | Role | Формат | Файлов | Hint values | Ограничение |
| --- | --- | --- | ---: | --- | --- |
| DNS | `TRAIN` | `csv` | 8 | benign, malware, phishing, spam | Использовать как inferred labels только через фиксированный mapping. |
| DNS | `TRAIN` | `pcap` | 4 | benign, malware, phishing, spam | Нужен packet parser и filename mapping. |
| DNS | `TRAIN` | `pcap.csv` | 14 | audio, benign, compressed, exe, image, text, video | Payload class не равен attack label без target policy. |
| DNS | `VALIDATION` | `pcap` | 5 | attack, benign | Filename mapping допустим для validation after audit. |
| DNS | `VALIDATION` | `txt` | 3 | unknown, benign | `unknown` не считать benign/attack автоматически. |
| DNS | `TEST` | `csv` | 1 | boolean-like `label_or_flag` | TEST только для evaluation; нужна schema policy. |

##### Readiness statuses

| Статус | Что означает для Stage Two |
| --- | --- |
| `READY_FOR_FEATURE_EXTRACTION` | Можно подключать к feature extraction после корректной нормализации; не означает наличие labels. |
| `NEEDS_CUSTOM_PARSER` | Нужен специализированный parser/decoder или binary/schema-aware layer. |
| `PARTIALLY_SUPPORTED` | Формат пригоден частично; parser должен различать под-схемы, служебные файлы или fixed schema. |
| `BROKEN_OR_EMPTY` | Bucket пустой или отсутствует; feature extraction невозможен до восстановления input. |

##### Правила для TRAIN / VALIDATION / TEST

| Role | Разрешено | Запрещено |
| --- | --- | --- |
| `TRAIN` | Обучение и fit preprocessing только после label-safe mapping. | Использовать weak labels как ground truth без статуса/уверенности. |
| `VALIDATION` | Проверка качества, threshold tuning только если это предусмотрено experiment design. | Смешивать с TRAIN artifacts. |
| `TEST` | Только финальная оценка/inference. | Training, fit scaler/encoder, feature selection, threshold tuning, filename heuristic label inference. |

##### Минимальный LabelResolver алгоритм

1. Сохранить inventory: domain, role, format, source_file, checksum, file_size.
2. На parsing этапе извлечь timestamp, host, ip, process/session/scenario identifiers, row/event/packet id.
3. Применить правила в порядке:
   - embedded column;
   - external label file (`ground_truth.csv`, `runs.csv`, attack labels);
   - filename/class hint;
   - scenario metadata;
   - IDS alert as weak label;
   - no match -> unlabeled.
4. При конфликте выставить `conflicting_label`, а не выбирать класс произвольно.
5. Для `TEST` разрешать labels только для evaluation после завершения training pipeline.

##### Связь с normalization

См. также:

- [../normalization/label_resolver.md](ru/normalization/label_resolver.md)
- [../normalization/data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md)
- [../normalization/traceability.md](ru/normalization/traceability.md)

---

### Источник: `docs/ru/analysis-dataset/parser_feature_recommendations.md`

[Открыть исходный файл](ru/analysis-dataset/parser_feature_recommendations.md)

#### Рекомендации для parser pipeline и feature extraction

Документ переводит результаты анализа датасетов в требования для Stage Two parser implementations, normalized event schema и feature extraction.

##### Общие требования

1. Routing должен учитывать `branch`, `role`, `source_format`, а не только расширение файла.
2. Raw files не изменяются.
3. `TRAIN`, `VALIDATION`, `TEST` обрабатываются раздельно.
4. Для больших line-oriented источников обязателен streaming/batch read.
5. Labels присоединяются отдельным label resolver layer с traceability.
6. Отсутствующий timestamp сохраняется как `timestamp=null`, `timestamp_type=missing` или `event_order`, если доступен порядок события.

##### Parser priorities

###### Высокий приоритет

| Parser | Форматы | Почему важно |
| --- | --- | --- |
| DNS packet parser | DNS `pcap`, DNS VALIDATION `pcap` | Нужен для packet-level DNS features и validation. |
| Host BSON parser | Host TEST `bson` | Крупный source behaviour sequences; нужен descriptor/event join по `I`. |
| Host JSON parser | Host TRAIN/TEST `json`, `json-1` | Смешанные JSON Lines, Mongo-style JSON, scenario reports. |
| Host syscall/trace parser | Host TEST/VALIDATION/TRAIN `txt`, `sc`, `ghc` | Большие sequence datasets, важны для behaviour-driven learning. |
| Host packet parser | Host VALIDATION `cap`/`pcap`/`pcapng`, Host TRAIN `pcap` | Network/hybrid validation и flow/packet features. |

###### Средний приоритет

| Parser | Форматы | Задача |
| --- | --- | --- |
| Host line log parser | `auth.log`, `info`, `log*`, `syslog*`, `messages*`, `mainlog*`, `mail-*` | Различать raw syslog, JSON-lines и scenario documents. |
| Host metric parser | `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `uptime.log` | Metric rows, annotation rows, nested schema variants. |
| CSV normalizers | DNS TEST `csv`, Host TRAIN/VALIDATION/TEST `csv` | Headerless/fixed schema, metadata CSV, external labels. |

###### Низкий риск / можно подключать раньше

| Источник | Причина |
| --- | --- |
| DNS `pcap.csv` | Стабильные headers, готов к feature extraction. |
| DNS VALIDATION `txt` | Простая domain-list структура. |
| Host filesystem/fsstat/service/socket/process summary metrics | JSON-lines/telemetry rows. |
| `netflow_day`, `netflow_ids`, `wls_day` | Line-oriented, но требуют streaming и external labels. |

##### Parser contracts by format family

| Семейство | Обработка входа | Normalized output | Граничные случаи |
| --- | --- | --- | --- |
| CSV | Schema detection, header/headerless support, fixed positional schemas. | Row events, flow events, label metadata if explicit. | Service CSV files, malformed list/dict fields, label CSV joins. |
| JSON/JSONL | Distinguish JSON Lines, multi-line reports, Mongo-style wrappers. | Event/metadata records with raw payload preserved. | `NumberLong(...)`, nested timestamps, scenario docs. |
| Logs/syslog | Line parser с извлечением timestamp/user/process. | Host log events, event type, component, severity. | Mixed raw syslog и JSON-lines под одним расширением. |
| Metrics | JSON-lines or structured telemetry extraction. | Metric events/windows by host/time/component. | Annotation rows and schema variants. |
| Traces | Streaming line/token parser. | Sequence events with `event_index`. | Missing timestamps; очень большое число файлов. |
| Packet captures | Binary parser. | Packet/flow/DNS events with packet timestamp. | Поврежденные captures, различия pcap/pcapng/cap, performance. |
| BSON | BSON stream decoder. | Sandbox event sequences with descriptor/event relation. | Descriptor-event join by `I`, nested `args`, ordering. |

##### Feature extraction map

| Feature group | Источники | Примеры |
| --- | --- | --- |
| `dns_features` | DNS CSV, pcap.csv, DNS packet captures, domain lists | Длина домена, entropy, qtype/rcode/ttl, query rate, unique subdomain ratio. |
| `host_syscall_features` | `txt`, `sc`, `ghc`, BSON sequence events | Syscall/API n-grams, transition probabilities, sequence length, file access indicators. |
| `host_eventlog_features` | syslog/auth/messages/mainlog/mail/info/logs, Windows/Sysmon JSON/WLS | Event type counts, auth success/failure, process chains, alert counts. |
| `host_metrics_features` | CPU/disk/filesystem/memory/network/process/service/socket metrics | Window aggregates, deltas, rates, peak values. |
| `network_flow_features` | `netflow_day`, `netflow_ids`, packet captures | Bytes/packets/duration/protocol/state/window counts. |
| `hybrid_features` | Correlated host + DNS + flow windows | Host process + network flow correlation, exfiltration windows. |
| `sequence_features` | syscall/API/log event order | LSTM/Transformer sequence inputs, n-gram vectors. |

##### Readiness-to-action mapping

| Readiness | Stage Two action |
| --- | --- |
| `READY_FOR_FEATURE_EXTRACTION` | Подключить parser, если он еще не реализован; `mark-ready` можно выполнять после parser coverage check. |
| `NEEDS_CUSTOM_PARSER` | Добавить parser class и registry entry до normalization. |
| `PARTIALLY_SUPPORTED` | Добавить schema detection/sub-parser routing; не считать формат однородным. |
| `BROKEN_OR_EMPTY` | Не нормализовать; проверить Stage One sort/save-sort и source bucket. |

##### Data quality checks to add

- Per-format row/event counts after normalization.
- Empty file and empty artifact checks.
- Schema drift report by branch/role/format.
- Label coverage by role/format/status.
- Покрытие timestamp и распределение `timestamp_type`.
- Метрики производительности parser для больших файлов.
- Split contamination check: no TRAIN/VALIDATION/TEST mixing.

##### Implementation guardrails

- TEST labels, even if present, are evaluation-only.
- Filename labels must be disabled or heavily restricted for TEST.
- Label/source/traceability fields должны быть исключены из model-ready X.
- `unknown` labels remain unknown until explicit mapping exists.
- Packet/BSON parsers must not load huge files fully into memory.
- Parser errors should produce `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED` or `UNSUPPORTED_FORMAT`, not silent success.

---

## Stage Two и нормализация

### Источник: `docs/ru/normalization/README.md`

[Открыть исходный файл](ru/normalization/README.md)

#### Stage Two / нормализация данных

Раздел описывает фактическую реализацию Stage Two: catalog ingestion, parser registry, нормализацию DNS/Host файлов в normalized events, запись Parquet artifacts, PostgreSQL Catalog, DuckDB/data quality/leakage checks и traceability. Документы предназначены для разработчика, который должен запускать pipeline, добавлять parser implementations и проверять, что данные не смешивают роли и не создают leakage.

##### Границы Stage Two

Stage Two начинается после Stage One, когда исходные файлы уже разложены в sorted/filter tree. Raw-файлы не изменяются: Stage Two читает их, регистрирует metadata в PostgreSQL и создает новые артефакты в `PATH_DATA_STORAGE`.

Фактически реализованные части:

| Область | Реализация | Документ |
| --- | --- | --- |
| CLI/routing | `manage.py`, `scripts/router_script.py`, `scripts/stage_two/cli.py` | [usage_guide.md](ru/normalization/usage_guide.md), [stage_two_commands.md](ru/normalization/stage_two_commands.md) |
| Storage bootstrap | `scripts/stage_two/storage/bootstrap.py` | [storage_architecture.md](ru/normalization/storage_architecture.md) |
| Catalog ingestion | `scripts/stage_two/ingestion/*` | [postgresql_catalog_schema.md](ru/normalization/postgresql_catalog_schema.md) |
| Parser registry/resolver | `scripts/stage_two/parser_registry/*` | [parser_strategy.md](ru/normalization/parser_strategy.md) |
| Parser development | `scripts/stage_two/parsers/*` | [parser_development_guide.md](ru/normalization/parser_development_guide.md) |
| Label resolver | `scripts/stage_two/labels/resolver.py` | [label_resolver.md](ru/normalization/label_resolver.md) |
| Normalized schema | `schemas/normalized/normalized_event_v1.json` | [normalized_event_schema.md](ru/normalization/normalized_event_schema.md) |
| Parquet/DuckDB | `scripts/stage_two/parquet/*`, `scripts/stage_two/duckdb/*` | [parquet_duckdb_artifacts.md](ru/normalization/parquet_duckdb_artifacts.md) |
| Quality checks | `scripts/stage_two/quality/checkers.py` | [data_quality_checks.md](ru/normalization/data_quality_checks.md) |
| Leakage prevention | feature/model-ready contracts, `LeakageChecker` | [data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md) |
| Traceability | `scripts/stage_two/traceability/service.py` | [traceability.md](ru/normalization/traceability.md) |
| Performance/runbooks | normalization options, large-file split, recovery steps | [performance_tuning.md](ru/normalization/performance_tuning.md), [runtime_resource_runbook.md](ru/normalization/runtime_resource_runbook.md) |

Не реализовано как отдельная CLI-команда в текущем роутере: полноценный build step для feature artifacts и model-ready artifacts. Для них есть contracts, writers/registry services и e2e dry-run, но operational CLI сейчас покрывает catalog, parser readiness, normalization, DuckDB checks, leakage checks и traceability.

##### Рекомендуемый порядок чтения

1. [usage_guide.md](ru/normalization/usage_guide.md) - как запустить Stage Two и какие команды реально поддерживает CLI.
2. [stage_two_commands.md](ru/normalization/stage_two_commands.md) - полный reference по командам normalization: входы, выходы, статусы, ошибки и проверки.
3. [storage_architecture.md](ru/normalization/storage_architecture.md) - что должно быть в `PATH_DATA_STORAGE`.
4. [postgresql_catalog_schema.md](ru/normalization/postgresql_catalog_schema.md) - какие metadata и связи хранятся в PostgreSQL.
5. [parser_strategy.md](ru/normalization/parser_strategy.md) и [parser_development_guide.md](ru/normalization/parser_development_guide.md) - как выбирается parser и как добавить новый.
6. [normalized_event_schema.md](ru/normalization/normalized_event_schema.md) и [label_resolver.md](ru/normalization/label_resolver.md) - контракт normalized event и правила labels.
7. [parquet_duckdb_artifacts.md](ru/normalization/parquet_duckdb_artifacts.md), [data_quality_checks.md](ru/normalization/data_quality_checks.md), [data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md), [traceability.md](ru/normalization/traceability.md) - артефакты, проверки и lineage.
8. [performance_tuning.md](ru/normalization/performance_tuning.md), [runtime_resource_runbook.md](ru/normalization/runtime_resource_runbook.md), [final_summary_template.md](ru/normalization/final_summary_template.md) - эксплуатация, восстановление и итоговая отчетность.

##### Основные инварианты

1. Raw-файлы датасетов не изменяются.
2. `TRAIN`, `VALIDATION` и `TEST` не смешиваются в одном normalized/feature/model-ready artifact.
3. `TEST` не используется для обучения, fit preprocessing, fit scaler, fit encoder, threshold tuning или feature selection.
4. PostgreSQL хранит metadata, статусы, связи, пути, хеши и отчеты; большие normalized/features/model-ready таблицы хранятся в Parquet.
5. DuckDB используется для аналитических SQL-проверок поверх Parquet.
6. Labels хранятся отдельно от X-признаков.
7. Leakage/source/label поля не должны попадать в model-ready `X` artifacts.
8. Все артефакты должны сохранять traceability: `raw -> normalized -> features -> model-ready`.
9. Отсутствующий label не означает benign.
10. Filename heuristics для `TEST` labels отключены.
11. Отсутствующий timestamp нельзя заменять текущим временем; нужно сохранять `timestamp = null` и `timestamp_type = "missing"` либо `event_order`, если доступен порядок события.

##### Основные команды

Все команды проходят через `manage.py`:

```bash
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage [dns|host|network|hybrid]
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two split-large-files --branch host --role TRAIN --format csv --max-part-size-mb 512 --apply --register
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Миграции и модульные проверки запускаются отдельно:

```bash
alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m scripts.db.smoke_check
python -m scripts.stage_two.readiness_check
python -m scripts.stage_two.e2e_dry_run
```

##### Pipeline

```mermaid
flowchart TD
    A["Stage One sorted/filter tree"] --> B["catalog-ingest"]
    B --> C["datasets, ingestion_runs, dataset_files"]
    C --> D["seed-parser-registry"]
    D --> E["parser-coverage / mark-ready"]
    E --> F["normalize-format / normalize-all / normalize-dns / normalize-host"]
    F --> G["parser_runs"]
    F --> H["parquet/normalized/..."]
    G --> I["normalized_artifacts"]
    H --> J["DuckDB views and checks"]
    I --> K["feature/model-ready contracts and registry services"]
    K --> L["feature_artifacts / model_ready_artifacts"]
    L --> M["leakage checks"]
    L --> N["trace-artifact"]
```

##### Терминология

| Термин | Значение |
| --- | --- |
| branch | Модальность или ветка данных: `dns`, `host`, `network`, `hybrid`. Нормализация сейчас поддерживает `dns` и `host`. |
| role | Split датасета: `TRAIN`, `VALIDATION`, `TEST`. `EXPERIMENTS` есть в DB constraint, но catalog scanner Stage Two активирует только `TRAIN/VALIDATION/TEST`. |
| source_format | Формат исходного файла: `csv`, `pcap`, `pcap.csv`, `json`, `txt`, `bson`, `auth.log`, `netflow_day` и т.д. |
| normalized event | Одна нормализованная запись по контракту `normalized_event/v1`. |
| parser run | Запуск parser для одного `dataset_files.id`. |
| artifact | Parquet или внешний файл, зарегистрированный в catalog metadata. |

---

### Источник: `docs/ru/normalization/usage_guide.md`

[Открыть исходный файл](ru/normalization/usage_guide.md)

#### Руководство запуска Stage Two normalization

Документ фиксирует фактический CLI слой: `manage.py` принимает `module`, `service`, `action`, `extra_args`, передает `stage-two` в `scripts.stage_two.cli.router_stage_two()`, а роутер вызывает конкретные service functions.

Полный reference по каждой Stage Two normalization команде, включая входы, выходы, статусы PostgreSQL, ошибки и проверки, находится в [stage_two_commands.md](ru/normalization/stage_two_commands.md).

##### Предварительные условия

Нужно настроить окружение:

```bash
export PATH_DATA_STORAGE=/absolute/path/to/stage-two-storage
export PATH_FOLDER_DATASETS_FILTER=/absolute/path/to/stage-one-filtered-or-sorted-tree
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/database
```

`DATABASE_URL` читается через `scripts/db/config.py`. Если переменной нет в окружении, код пробует загрузить `.env` из корня проекта.

##### Базовый порядок запуска

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

##### Команды Stage Two

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

##### `mark-ready`

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

##### `normalize-format`

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

##### `normalize-all`

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

##### Legacy-команды

```bash
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

Эти команды оставлены для совместимости. Для воспроизводимых запусков предпочтительны `normalize-format` или `normalize-all`, потому что они явно задают branch/role/format и performance options.

##### Разделение больших файлов

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

##### Проверки

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

`run-duckdb-checks` строит views `normalized_all`, `features_all`, `model_ready_all` поверх Parquet и проверяет row counts, required columns, split contamination и schema mismatch. `run-leakage-checks` проверяет запретные X columns, отсутствие `TEST` в training/preprocessing fit и регистрирует CRITICAL нарушения.

##### Trace artifact

```bash
python manage.py stage-two trace-artifact 123
python manage.py stage-two trace-artifact parquet/model_ready/tabular/dns/TRAIN/schema=v1/X_train.parquet
```

Числовой аргумент трактуется как `model_ready_artifacts.id`, строковый путь - как `model_ready_artifacts.artifact_path`. Команда требует, чтобы у model-ready artifact был `feature_artifact_id`, а у feature artifact - `normalized_artifact_id`; иначе traceability chain считается разорванной.

##### Модульные проверки

Эти проверки не зарегистрированы как `manage.py stage-two` commands, но реализованы как Python modules:

```bash
python -m scripts.db.smoke_check
python -m scripts.stage_two.readiness_check
python -m scripts.stage_two.e2e_dry_run
```

`readiness_check` проверяет миграции, storage paths, counts catalog tables, parser coverage, normalized/feature/model-ready registration, quality/leakage reports, traceability и raw file hashes. `e2e_dry_run` создает synthetic DNS/Host samples под `temp_data`, прогоняет ingestion, seed, normalization, feature/model-ready registry services, DuckDB/leakage checks и traceability.

##### Типовые ошибки

| Симптом | Причина | Действие |
| --- | --- | --- |
| `DATABASE_URL must be configured` | Нет `DATABASE_URL` в окружении или `.env`. | Настроить `DATABASE_URL`. |
| `PATH_DATA_STORAGE must be configured` | Storage root не задан. | Задать `PATH_DATA_STORAGE`, затем `bootstrap-storage`. |
| `No parser available` / `UNSUPPORTED_FORMAT` | В `parser_registry` нет активного parser для `branch/role/source_format`. | Проверить `parser-coverage`, добавить parser или registry entry. |
| Empty DuckDB views | Parquet layer пустой или paths не созданы. | Проверить `normalized_artifacts` и storage paths. |
| Leakage CRITICAL | X artifact содержит label/source fields или TEST участвует в fit/training. | Пересобрать artifact с корректным contract. |

---

### Источник: `docs/ru/normalization/stage_two_commands.md`

[Открыть исходный файл](ru/normalization/stage_two_commands.md)

#### Команды Stage Two normalization

Документ описывает реализованные команды Stage Two normalization и операционный порядок запуска. Источники проверки: `manage.py`, `scripts/router_script.py`, `scripts/stage_two/cli.py`, сервисы `scripts/stage_two/*` и файл `stage_two_dns_host_normalization_commands.txt`.

Главная точка входа:

```bash
python manage.py stage-two <command> [args]
```

`manage.py` принимает `module`, `service`, `action`, `extra_args`; `scripts/router_script.py` направляет `module=stage-two` в `scripts.stage_two.cli.router_stage_two()`. Неизвестная Stage Two команда возвращает ошибку `unknown Stage Two command`.

Сверка с кодом от 2026-07-04: fallback-текст из `config.manage_commands` не является полным help по Stage Two. В нем нет части новых router-команд, включая `parser-coverage`, `mark-ready`, `normalize-format`, `normalize-all`, `benchmark-normalization` и `split-large-files`. Источник истины по реализованным Stage Two командам - `scripts/stage_two/cli.py`.

##### Полный порядок запуска

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

##### Команды и операционные шаги

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

##### `bootstrap-storage`

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

##### `catalog-ingest`

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

##### `seed-parser-registry`

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

##### `parser-coverage`

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

##### Операционный шаг `READY_FOR_PARSING`

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

##### `split-large-files`

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

##### `normalize-format`

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

##### `normalize-all`

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

##### `normalize-dns` и `normalize-host`

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

##### `run-duckdb-checks`

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

##### `run-leakage-checks`

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

##### `trace-artifact`

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

##### Команды из операционного runbook

`stage_two_dns_host_normalization_commands.txt` содержит практические batch-команды для оставшихся DNS/Host форматов. Они соответствуют реализованным CLI-командам:

- `mark-ready --dry-run/--apply` для каждого `branch/role/source_format`;
- `split-large-files` для больших line-based files;
- `normalize-format` с `--workers`, `--batch-size`, `--max-output-part-rows`, `--packet-mode`, `--sample-size`, `--resume`;
- `parser-coverage`, `run-duckdb-checks`, `run-leakage-checks` как проверки после запуска.

Файл содержит Windows-specific команды `cd` и `conda activate`; они являются инструкциями окружения, а не частью CLI проекта. Команда `python -m scripts.stage_two.readiness_check` реализована как module check, но не зарегистрирована в `router_stage_two`.

##### Инварианты запуска

1. Raw-файлы не изменяются; Stage Two создает metadata и новые artifacts.
2. `TRAIN`, `VALIDATION`, `TEST` обрабатываются отдельными bucket-командами.
3. `TEST` не участвует в fit/training/tuning.
4. Labels не являются X features.
5. Отсутствующий label не означает benign.
6. Отсутствующий timestamp нельзя заменять текущим временем.
7. Все artifacts должны сохранять traceability `raw -> normalized -> features -> model-ready`.
##### Performance commands и profiles

Текущий CLI также включает `benchmark-normalization` и resource profiles для `normalize-format` / `normalize-all`.

###### `benchmark-normalization`

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

###### Resource profiles

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

###### Безопасные PCAP/BSON примеры

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

###### Большие line-based files

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

###### Обязательные gates после performance runs

`normalize-format` сохраняет post-run validation summary. После performance runs также запускайте:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Если `run-leakage-checks` возвращает CRITICAL, не используйте затронутые feature/model-ready artifacts.

---

### Источник: `docs/ru/normalization/runtime_resource_runbook.md`

[Открыть исходный файл](ru/normalization/runtime_resource_runbook.md)

#### Runbook по runtime-ресурсам

Runbook описывает диагностику Stage Two normalization без изменения raw files.

##### Быстрый чеклист статуса

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

##### Если storage не готов

Симптомы:

- `PATH_DATA_STORAGE must be configured`;
- отсутствующие директории в readiness report;
- DuckDB views пустые из-за отсутствующих Parquet roots.

Действия:

```bash
export PATH_DATA_STORAGE=/absolute/path/to/stage-two-storage
python manage.py stage-two bootstrap-storage
python -m scripts.stage_two.readiness_check
```

##### Если catalog пустой

Симптомы:

- `catalog_counts.dataset_files = 0`;
- `parser-coverage` нечего проверять;
- `mark-ready` не находит files.

Действия:

```bash
export PATH_FOLDER_DATASETS_FILTER=/absolute/path/to/stage-one-filtered-or-sorted-tree
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
```

Проверьте, что input tree содержит `TRAIN`, `VALIDATION`, `TEST`; scanner не активирует произвольные роли.

##### Если parser отсутствует

Симптомы:

- `UNSUPPORTED_FORMAT`;
- `parser-coverage` показывает uncovered combination;
- `normalize-format` не создает normalized artifact.

Действия:

1. Проверить `branch/role/source_format` в `dataset_files`.
2. Проверить `parser_registry` после `seed-parser-registry`.
3. Добавить parser class или registry entry.
4. Перезапустить:

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --apply
```

##### Если normalization падает

Действия:

```bash
python manage.py stage-two normalize-format \
  --branch <branch> \
  --role <ROLE> \
  --format <format> \
  --limit 10 \
  --workers 1
```

После ошибки проверить:

- `parser_runs.status`, counters, error samples;
- `dataset_files.status` и `error_message`;
- parser-specific warnings;
- schema mismatch report;
- размер файла и необходимость `split-large-files`.

Для больших line-based files:

```bash
python manage.py stage-two split-large-files \
  --branch <branch> \
  --role <ROLE> \
  --format <format> \
  --max-part-size-mb 512 \
  --apply \
  --register
```

##### Если проверки DuckDB завершились ошибкой

Проверить:

- существуют ли Parquet files под `PATH_DATA_STORAGE/parquet`;
- совпадают ли paths в catalog и на диске;
- есть ли required columns;
- не смешаны ли roles;
- не записаны ли пустые artifacts вместо ошибок parser.

Запуск:

```bash
python manage.py stage-two run-duckdb-checks
```

##### Если leakage checks завершились ошибкой

Проверить:

- model-ready `X` не содержит forbidden columns;
- preprocessing artifacts имеют `fitted_on_role = TRAIN`;
- `TEST` не используется в training context;
- unlabeled events не превращены в benign.

Запуск:

```bash
python manage.py stage-two run-leakage-checks
```

CRITICAL leakage report должен блокировать использование artifact.

##### Если traceability chain разорвана

Запуск:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
python -m scripts.stage_two.readiness_check
```

Проверить links:

```text
model_ready -> feature -> normalized -> parser_run -> dataset_file -> dataset
```

Если `feature_artifact_id` или `normalized_artifact_id` отсутствует, artifact нельзя считать полностью traceable.

##### Несовпадение raw hash

Readiness check пересчитывает hashes для `dataset_files.file_path`. Mismatch означает, что raw file изменился после ingestion или catalog указывает не на тот файл.

Действия:

1. Не перезаписывать catalog вручную без audit.
2. Проверить source path и backup.
3. Повторить `catalog-ingest`, если raw tree официально обновлен.
4. Пересобрать downstream artifacts, потому что normalized/features/model-ready могли быть созданы из старого содержимого.
##### Performance runbook для текущего железа

Целевое железо:

- Intel Core i7-14700KF.
- 64 GB DDR5 RAM.
- Samsung M.2 SSD 2 TB.
- MSI GeForce RTX 5060 Ti 16 GB.

Raw normalization ориентирована на CPU. GPU по умолчанию не используется для raw parsers; оставляйте GPU для feature/model-ready/training layers, пока нет отдельного parser backend с проверенной корректностью.

###### Цель

- Full Stage Two normalization target: `17 GB <= 3 hours`.
- Требуемая скорость: около `5.67 GB/hour`.
- Ожидаемый target для line-based formats на этом железе: `10-20+ GB/hour` после benchmark validation.

###### Безопасный порядок запуска

1. Проверить parser coverage и подготовить один точный bucket.
2. Запустить `benchmark-normalization` на 5-10% файлов.
3. Начать с `safe` или `balanced`.
4. Переходить на `fast` только после проверки parser reports, DuckDB checks, leakage checks, RAM, DB connections и SSD write behavior.
5. Использовать `aggressive` только для line-based formats после чистого `fast` run.
6. Full bucket запускать с `--resume`.
7. Запустить post-run gates:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

###### Примеры команд

Benchmark:

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Line-based full run:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --resume
```

PCAP safe run:

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume
```

BSON safe run:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

###### Troubleshooting performance runs

| Проблема | Что проверить | Recovery |
| --- | --- | --- |
| PostgreSQL timeout | long transactions, locks, slow catalog writes | уменьшить `--workers`, использовать `safe`, перезапустить с `--resume` |
| too many DB connections | process workers vs DB pool size | ограничить workers до `4-8`, не использовать `aggressive`, проверить worker-local sessions |
| memory pressure | batch size, output part rows, binary formats | уменьшить `--batch-size`, уменьшить `--max-output-part-rows`, split для line-based files |
| SSD throttling | high concurrent writes, temperature, hashing | уменьшить workers, отключить output hashing на итерациях, разделить большие buckets |
| too many small files | scheduler и catalog overhead | использовать bounded execution, группировать exact format, избегать mixed all-branch runs |
| parser errors | parser run reports, error samples, malformed rows | исправить parser/schema handling; не считать malformed rows успешными silently |
| empty DuckDB views | нет Parquet roots или неверный storage path | проверить `PATH_DATA_STORAGE`, artifact paths и `run-duckdb-checks` report |
| leakage critical | forbidden X columns или TEST в training artifacts | остановить training use, проверить leakage report, пересобрать feature/model-ready artifacts |

###### Safety rules

- Не изменять raw dataset files.
- Не смешивать `TRAIN`, `VALIDATION`, `TEST`.
- Не использовать `TEST` для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
- PostgreSQL остается catalog/control plane, Parquet хранит большие данные.
- Labels и path/source/scenario fields не попадают в model-ready X.
- Missing labels не считаются benign.
- Missing timestamps не заменяются current time.
- Traceability сохраняется от raw file до normalized, features и model-ready artifacts.

---

### Источник: `docs/ru/normalization/performance_tuning.md`

[Открыть исходный файл](ru/normalization/performance_tuning.md)

#### Настройка производительности normalization

Документ описывает только реализованные runtime options из `scripts/stage_two/normalization/options.py` и `scripts/stage_two/cli.py`.

##### Опции нормализации

| CLI option | Default | Назначение |
| --- | --- | --- |
| `--workers` | `STAGE_TWO_DEFAULT_WORKERS` (`1`) | Количество parallel worker processes для `normalize-format`/`normalize-all`. |
| `--batch-size` | `STAGE_TWO_DEFAULT_BATCH_SIZE` (`50000`) | Размер batch при parser batch processing. |
| `--max-output-part-rows` | `STAGE_TWO_MAX_OUTPUT_PART_ROWS` (`50000`) | Максимум rows в output part, если service делит output. |
| `--resume` | `false` | Пропускать уже успешно нормализованные files. |
| `--hash-output-artifacts` | `false` | Считать SHA-256 для output Parquet artifacts. |
| `--packet-mode` | `packet-summary` | Режим packet parsing: `packet-summary`, `dns-only`, `sample`. |
| `--sample-size` | unset | Обязателен для `--packet-mode sample`. |
| `--resource-profile` | unset | Optional preset: `safe`, `balanced`, `fast` или `aggressive`. |
| `--engine` | `cpu` | Допустимые значения: `cpu`, `gpu`, `auto`; raw Stage Two parsers все равно работают на CPU, пока не реализован отдельный parser-specific backend. |

Порядок resolution:

1. Стартовые значения берутся из constants в `config.py`.
2. Если указан `--resource-profile`, применяются значения profile.
3. Явные CLI overrides вроде `--workers` и `--batch-size` имеют приоритет над profile.
4. Для `normalize-format` и `benchmark-normalization` затем применяется format policy к тем значениям, которые пользователь явно не переопределил.

`normalize-all` получает общие runtime options из defaults/profile/explicit flags, но текущий CLI route не применяет per-format policy к каждой группе перед вызовом runner.

Пример:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --limit 10000 \
  --workers 4 \
  --batch-size 50000 \
  --max-output-part-rows 50000 \
  --resume
```

##### Выбор `--workers`

`--workers > 1` включает `ProcessPoolExecutor` в normalization runner. Это полезно для независимых файлов, но увеличивает:

- количество открытых DB connections;
- конкуренцию за диск;
- memory pressure при больших parser outputs;
- сложность диагностики parser errors.

Практический порядок:

1. Начать с `--workers 1 --limit 10`.
2. Проверить parser status, Parquet output и DuckDB checks.
3. Увеличивать workers постепенно.
4. Для binary PCAP/PCAPNG не повышать workers без контроля RAM/IO.

##### Packet modes

| Mode | Когда использовать |
| --- | --- |
| `packet-summary` | Default для безопасного summary parsing packet captures. |
| `dns-only` | Когда нужен DNS extraction из packet captures и parser это поддерживает. |
| `sample` | Для первичной оценки больших PCAP/PCAPNG; требует `--sample-size`. |

Если `packet-mode = sample` и `sample-size` не задан, validation options выбросит ошибку.

##### Разделение больших файлов

Для больших line-based files используйте:

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TRAIN \
  --format csv \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Splitter поддерживает text/line formats и не предназначен для `cap`, `pcap`, `pcapng`, `bson`.

Риски:

- JSON arrays/objects могут быть небезопасны для line split;
- header handling нужно проверять через `--header auto|yes|no`;
- без `--register` chunks не появятся в catalog.

##### Хеширование output artifacts

`--hash-output-artifacts` повышает проверяемость, но добавляет IO cost, потому что файл нужно прочитать после записи. Для smoke/iteration можно оставить выключенным; для финальных artifacts лучше включать.

##### Resume

`--resume` пропускает файлы, для которых уже есть успешный normalized artifact. Это не заменяет data quality checks: после resume все равно нужно запускать:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

##### Ограничения

- Performance options не должны менять contracts и labels.
- Нельзя объединять роли ради ускорения.
- Нельзя использовать `TEST` для подбора batch/feature/preprocessing решений, если это влияет на training pipeline.
- Для mixed CSV/JSON schemas лучше уменьшить batch size и сначала прогнать `--limit`.
##### Обновление performance architecture

Stage Two теперь поддерживает resource profiles, format-specific policy, bounded multiprocessing, streaming parser batches, chunk-aware large-file processing, atomic Parquet writes, benchmark reports и post-run quality gates.

###### Performance target

- Цель по датасету: `17 GB <= 3 hours`.
- Требуемая скорость: около `5.67 GB/hour`.
- Целевая скорость для текущего железа: `10-20+ GB/hour` для line-based formats при нормальном состоянии RAM, PostgreSQL, SSD и parser errors.

Текущее железо:

- CPU: Intel Core i7-14700KF.
- RAM: 64 GB DDR5.
- Storage: Samsung M.2 SSD 2 TB.
- GPU: MSI GeForce RTX 5060 Ti 16 GB.

GPU зарезервирован для feature/model-ready/training layers. Raw normalization parsers по умолчанию работают на CPU; PCAP/BSON/raw log parsing не переносится на GPU без отдельного backend и проверок корректности.

###### Resource profiles

Используйте `--resource-profile safe|balanced|fast|aggressive` с `normalize-format`, `normalize-all` и `benchmark-normalization`.

| Profile | workers | batch_size | max_output_part_rows | packet_batch_size | hash_output_artifacts |
| --- | ---: | ---: | ---: | ---: | --- |
| `safe` | 4 | 50000 | 100000 | 50000 | false |
| `balanced` | 8 | 100000 | 250000 | 50000 | false |
| `fast` | 12 | 200000 | 500000 | 50000 | false |
| `aggressive` | 14 | 300000 | 750000 | 50000 | false |

CLI arguments имеют приоритет над profile. Пример: `--resource-profile fast --workers 6` дает `workers=6`, остальные параметры берутся из `fast`.

CLI печатает `resolved_runtime_settings` перед запуском normalization. Для `aggressive` warning является эксплуатационным предупреждением: контролируйте RAM, DB connections, parser failures и SSD throttling.

###### Format policy

Если пользователь явно не указал runtime параметры, `normalize-format` и `benchmark-normalization` применяют format policy после profile resolution:

- быстрые line-based formats (`txt`, `sc`, `ghc`, log/syslog/messages/mainlog, `wls_day`, metric logs): больше workers и batch size;
- CSV / `pcap.csv` / NetFlow: умеренно высокие workers и большие batches;
- JSON / JSONL (`json`, `json-1`): умеренные workers и batches;
- BSON: низкое число workers;
- PCAP / PCAPNG / CAP: низкое число workers, `packet_batch_size=50000`, default `packet_mode=packet-summary`.

Явные CLI значения не перезаписываются policy. Для `normalize-all` с mixed/risky ready groups используйте conservative explicit settings или conservative profile.

###### Рекомендуемый порядок

1. Готовить к запуску один точный bucket: `branch/role/source_format`.
2. Сначала benchmark на 5-10% данных: сначала `--dry-run`, затем небольшой actual run.
3. Начинать с `safe` или `balanced`.
4. Переходить на `fast` только после проверки DuckDB, leakage, parser errors, RAM, DB connections и SSD.
5. Использовать `aggressive` только для line-based formats после чистых проверок.
6. Full run запускать с `--resume`.
7. После run запускать DuckDB, leakage и readiness checks.

###### Команды

Benchmark 5-10%:

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Split большого line-based файла:

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TEST \
  --format txt \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Быстрая normalization для line-based формата:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --resume
```

PCAP с безопасными настройками:

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume
```

BSON с безопасными настройками:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

Post-run checks:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

###### Safety invariants

- Raw files не изменяются.
- `TRAIN`, `VALIDATION`, `TEST` не смешиваются в catalog, Parquet paths, features и model-ready artifacts.
- `TEST` не используется для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
- PostgreSQL остается control plane; большие normalized/features/model-ready данные хранятся в Parquet.
- Labels и source/path/scenario/dataset role fields не попадают в model-ready X.
- Отсутствующий label не считается benign.
- Отсутствующий timestamp не заменяется текущим временем.
- Parser errors остаются явными: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `UNSUPPORTED_FORMAT`.
- Traceability сохраняется по цепочке `raw -> normalized -> features -> model-ready`.

###### Troubleshooting

| Симптом | Вероятная причина | Действие |
| --- | --- | --- |
| PostgreSQL timeout | слишком много workers или медленные catalog updates | уменьшить `--workers`, использовать `safe`, проверить DB locks/pool, перезапустить с `--resume` |
| too many DB connections | workers превышают capacity БД | ограничить workers до `4-8`, не использовать `aggressive`, проверить per-worker sessions |
| memory pressure | слишком большой batch/output part или binary parser load | уменьшить `--batch-size` и `--max-output-part-rows`; split для line-based files |
| SSD throttling | слишком много concurrent writes или hashing | уменьшить workers, не включать `--hash-output-artifacts` на итерациях, проверить температуру SSD |
| too many small files | overhead futures/DB/filesystem | использовать bounded executor, запускать точный format bucket, держать `--resume` |
| parser errors | malformed rows или новая schema variant | читать parser run report и error samples; failed rows не скрывать |
| empty DuckDB views | нет Parquet, неверный `PATH_DATA_STORAGE` или failed normalization | выполнить `bootstrap-storage`, проверить artifact paths, запустить `run-duckdb-checks` |
| leakage critical | forbidden X columns или TEST contamination | заблокировать artifact use, проверить `run-leakage-checks`, пересобрать features/model-ready |

---

### Источник: `docs/ru/normalization/storage_architecture.md`

[Открыть исходный файл](ru/normalization/storage_architecture.md)

#### Архитектура storage Stage Two

Stage Two хранит большие данные вне PostgreSQL. Корень задается переменной `PATH_DATA_STORAGE`, а `bootstrap-storage` создает обязательную структуру директорий через `scripts/stage_two/storage/bootstrap.py`.

##### Назначение `PATH_DATA_STORAGE`

`PATH_DATA_STORAGE` - отдельный storage root для Stage Two artifacts:

- Parquet normalized/features/model-ready tables;
- DuckDB SQL files, exports и локальные `.duckdb` databases;
- runtime logs;
- temp data для ingestion/parser/normalization/DuckDB;
- backups catalog metadata;
- runtime schema copies;
- reports на русском и английском.

Raw dataset files не копируются в `PATH_DATA_STORAGE` при catalog ingestion. Их путь и хеш сохраняются в PostgreSQL (`dataset_files.file_path`, `dataset_files.file_hash_sha256`).

##### Базовая структура

```text
PATH_DATA_STORAGE/
  postgres/
  pgadmin/
  parquet/
    normalized/
    features/
    model_ready/
  duckdb/
    sql/
    exports/
  logs/
    stage-two/
  backups/
    postgres_catalog/
    metadata_exports/
  temp_data/
    ingestion/
    parser_runs/
    normalization/
    duckdb/
  schemas/
    normalized/
    features/
    model_ready/
  reports/
    ru/
      stage-two/
        parser/
        normalization/
        quality/
        leakage/
        schema_mismatch/
    en/
      stage-two/
        parser/
        normalization/
        quality/
        leakage/
        schema_mismatch/
  config/
```

`StorageBootstrapper.required_relative_paths()` также создает role-aware поддиректории для normalized/features/model-ready layers, чтобы `TRAIN`, `VALIDATION` и `TEST` не смешивались.

##### Parquet layers

| Layer | Путь | Кто пишет |
| --- | --- | --- |
| normalized | `parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` | `ParquetArtifactWriter.write_normalized()` через DNS/Host normalization services |
| features | `parquet/features/{feature_group}/{role}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet` | `FeatureArtifactWriter.write_and_register()` |
| model-ready | `parquet/model_ready/{artifact_type}/{branch}/{role}/schema={schema_version}/{file_name}` | `ModelReadyRegistryService.write_table_artifact()` |

В текущем CLI есть команды normalization и checks. Полноценная CLI-команда feature/model-ready build не реализована; соответствующий слой представлен contracts/writers/registry services.

##### Reports

| Report group | Примеры файлов | Кто пишет |
| --- | --- | --- |
| parser | coverage/status reports | parser coverage/status tools |
| normalization | parser run summaries | normalization services/runners |
| quality | `duckdb_analytics_report.json`, data quality reports | `DuckDBAnalyticsService`, `DataQualityChecker` |
| leakage | leakage reports RU/EN | `LeakageChecker` |
| stage-two root | readiness/e2e reports | `readiness_check`, `e2e_dry_run` |

`DuckDBAnalyticsService` сохраняет JSON report в `reports/en/stage-two/quality/duckdb_analytics_report.json`. `DataQualityChecker` и `LeakageChecker` сохраняют отчеты в RU/EN report roots.

##### Temp data

`temp_data` используется для временных результатов ingestion, parser runs, normalization и DuckDB. `e2e_dry_run` создает synthetic workspace под:

```text
temp_data/stage_two_e2e_dry_run/
```

Данные из `temp_data` нельзя считать source of truth. Source of truth для metadata - PostgreSQL Catalog, для больших таблиц - Parquet artifacts.

##### Config и schemas

| Путь | Назначение |
| --- | --- |
| `config/label_mapping_rules.json` | Внешние label mapping rules, если файл создан в storage. |
| `schemas/normalized/` | Runtime schema copies для normalized layer. |
| `schemas/features/` | Runtime schema copies для feature layer. |
| `schemas/model_ready/` | Runtime schema copies для model-ready layer. |

Проектные schema contracts находятся в репозитории:

```text
schemas/normalized/normalized_event_v1.json
schemas/features/feature_artifact_v1.json
schemas/model_ready/model_ready_v1.json
```

##### Ограничения

- Storage bootstrap создает директории, но не запускает PostgreSQL и не применяет Alembic migrations.
- PostgreSQL хранит пути к artifacts, но не хранит большие normalized/features/model-ready таблицы.
- Удаление или перенос файлов в `PATH_DATA_STORAGE/parquet` ломает `normalized_artifacts`, `feature_artifacts`, `model_ready_artifacts` и traceability.
- `PATH_FOLDER_DATASETS_FILTER` и `PATH_DATA_STORAGE` должны быть разными зонами ответственности: первая содержит input tree, вторая - Stage Two outputs.

---

### Источник: `docs/ru/normalization/postgresql_catalog_schema.md`

[Открыть исходный файл](ru/normalization/postgresql_catalog_schema.md)

#### PostgreSQL Catalog и SQLAlchemy слой

PostgreSQL Catalog хранит metadata, статусы, связи, пути, хеши и отчеты Stage Two. Большие normalized/features/model-ready таблицы не пишутся в PostgreSQL: они сохраняются как Parquet в `PATH_DATA_STORAGE`, а catalog хранит только ссылки и агрегированную metadata.

##### Где находится код

| Компонент | Путь |
| --- | --- |
| DB settings | `scripts/db/config.py` |
| Engine/session | `scripts/db/session.py` |
| Models | `scripts/db/models/*` |
| Constants/status values | `scripts/db/models/constants.py` |
| Repositories | `scripts/db/repositories/*` |
| Alembic migrations | `scripts/db/migrations/*` |
| Smoke check | `scripts/db/smoke_check.py` |

`session_scope()` создает SQLAlchemy session, делает `commit()` при успешном выходе и `rollback()` при исключении.

##### Миграции и smoke check

```bash
alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m scripts.db.smoke_check
```

Smoke check создает временные записи внутри транзакции и проверяет:

- unique/check constraints;
- создание `datasets`, `ingestion_runs`, `dataset_files`;
- parser run lifecycle;
- регистрацию normalized, feature, preprocessing, model-ready artifacts;
- запрет `TEST` для preprocessing fit;
- регистрацию quality report.

##### Основные constraints

| Constraint group | Значения |
| --- | --- |
| branch | `dns`, `host`, `network`, `hybrid` |
| active dataset role | `TRAIN`, `VALIDATION`, `TEST` |
| DB role values | `TRAIN`, `VALIDATION`, `TEST`, `EXPERIMENTS` |
| file status | `DISCOVERED`, `REGISTERED`, `CHANGED`, `EMPTY_FILE`, `UNSUPPORTED_FORMAT`, `READY_FOR_PARSING`, `PARSED`, `PARTIALLY_PARSED`, `FAILED`, `SKIPPED` |
| run status | `PENDING`, `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED` |
| parser run status | `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED` |
| schema layer | `normalized`, `features`, `model_ready` |
| label status | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label` |
| quality severity | `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

Catalog scanner Stage Two активирует только `TRAIN`, `VALIDATION`, `TEST`. `EXPERIMENTS` существует как DB value, но не должен попадать в основной normalization pipeline.

##### Таблицы

###### `datasets`

Назначение: логическая группа файлов одного dataset/branch/role/source group.

Пишут: `CatalogIngestionService`, DB smoke check.  
Читают: normalization services, artifact registration, readiness checks.

Ключевые поля: `id`, `name`, `slug`, `branch`, `role`, `source_group`, `root_path`, timestamps/metadata.

Связи: `datasets.id -> dataset_files.dataset_id`, `normalized_artifacts.dataset_id`, `feature_artifacts.dataset_id`.

###### `ingestion_runs`

Назначение: запуск сканирования input tree.

Пишут: `CatalogIngestionService`.  
Читают: diagnostics/readiness.

Ключевые поля: `id`, `root_path`, `root_path_kind`, `branch`, `role`, counters, `status`, timestamps, error fields.

###### `dataset_files`

Назначение: metadata raw/input файла, включая путь, размер, hash, role, branch, source_format и lifecycle status.

Пишут: catalog ingestion, large-file splitter при `--register`, status tools.  
Читают: parser resolver, normalization runners/services, readiness raw hash check.

Ключевые поля: `dataset_id`, `ingestion_run_id`, `file_path`, `relative_path`, `file_name`, `file_extension`, `source_format`, `file_size_bytes`, `file_hash_sha256`, `role`, `branch`, `status`, `error_message`, `metadata_json`.

Статусы: `REGISTERED` после ingestion, `READY_FOR_PARSING` после `mark-ready`, `PARSED`/`PARTIALLY_PARSED`/`FAILED` после normalization, `UNSUPPORTED_FORMAT` при отсутствии parser.

###### `parser_registry`

Назначение: declarative registry parser implementations.

Пишут: `ParserRegistrySeeder`.  
Читают: `ParserResolver`, normalization services, parser coverage, readiness.

Ключевые поля: `parser_name`, `parser_version`, `branch`, `source_format`, `supported_role`, `priority`, `normalized_schema_name`, `normalized_schema_version`, `parser_module`, `parser_class`, `is_active`, `config_json`.

Resolver выбирает active parser по `branch/source_format`, role-specific entry или `supported_role IS NULL`, сортирует по `priority` и `id`.

###### `schema_versions`

Назначение: catalog registry schema contracts.

Пишут: parser registry seed, repositories/smoke.  
Читают: parser runs, readiness, normalization.

Ключевые поля: `schema_name`, `schema_version`, `layer`, `branch`, `schema_path`, `schema_hash_sha256`, `is_active`.

###### `parser_runs`

Назначение: один запуск parser для одного `dataset_files.id`.

Пишут: DNS/Host normalization services.  
Читают: artifact registration, traceability, readiness.

Ключевые поля: `file_id`, `parser_registry_id`, `schema_version_id`, `parser_name`, `parser_version`, `status`, counters (`rows_read`, `rows_parsed`, `rows_failed`, `events_emitted`), `output_parquet_path`, error samples/timestamps.

Статусы: `RUNNING`, затем `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED` или `SKIPPED`.

###### `normalized_artifacts`

Назначение: metadata normalized Parquet artifact.

Пишут: `ParquetArtifactWriter.register_normalized_artifact()`.  
Читают: feature writer/registry services, DuckDB/readiness, traceability.

Ключевые поля: `dataset_id`, `file_id`, `parser_run_id`, `schema_version_id`, `role`, `branch`, `modality`, `source_format`, `normalized_path`, `schema_name`, `schema_version`, `row_count`, `event_count`, `file_size_bytes`, `content_hash_sha256`, `status`.

###### `feature_artifacts`

Назначение: metadata feature Parquet artifact.

Пишут: `FeatureArtifactWriter.write_and_register()`.  
Читают: model-ready registry, leakage checks, readiness, traceability.

Ключевые поля: `dataset_id`, `normalized_artifact_id`, `role`, `branch`, `feature_group`, `feature_path`, `feature_schema_name`, `feature_schema_version`, `row_count`, `sample_count`, `feature_count`, `excluded_columns_json`, `label_distribution_json`, `status`.

В production traceability `normalized_artifact_id` должен быть заполнен. Readiness check считает artifact без этой связи ошибкой.

###### `preprocessing_artifacts`

Назначение: metadata scaler/encoder/other preprocessing objects.

Пишут: `ModelReadyRegistryService.register_preprocessing_artifact()`.  
Читают: model-ready registry, leakage checks/readiness.

Ключевые поля: `branch`, `feature_group`, `preprocessing_type`, `artifact_path`, `fitted_on_role`, `fitted_on_feature_artifact_id`, `schema_version`, `object_version`, `columns_json`, `params_json`, `status`.

Ограничение: `fitted_on_role` должен быть `TRAIN`. Код отклоняет `TEST`.

###### `model_ready_artifacts`

Назначение: metadata model-ready X/y/sequence/split/preprocessing tables or files.

Пишут: `ModelReadyRegistryService.write_table_artifact()` и `register_external_artifact()`.  
Читают: leakage checks, traceability, readiness.

Ключевые поля: `feature_artifact_id`, `preprocessing_artifact_id`, `role`, `branch`, `data_type`, `artifact_path`, `schema_name`, `schema_version`, `sample_count`, `feature_count`, `excluded_columns_json`, `label_distribution_json`, `sequence_length`, `status`.

`data_type` поддерживает `X`, `y`, `sequence`, `split_index`, `preprocessing_metadata`. Для `X` registry validates forbidden leakage columns.

###### `label_mapping_rules`

Назначение: explicit/external rules для label resolver.

Пишут: `LabelRepository` или конфигурационные загрузчики, если используются в сценарии.  
Читают: `LabelResolver`.

Ключевые поля: branch/role/source_format matching, pattern/rule payload, canonical label fields, confidence/status, active flag.

Правило: отсутствие matching label rule не означает benign; событие остается unlabeled.

###### `data_quality_reports`

Назначение: metadata quality/leakage/DuckDB reports.

Пишут: `DuckDBAnalyticsService.register_report()`, `DataQualityChecker`, `LeakageChecker`, smoke/e2e checks.  
Читают: readiness, audit/reporting.

Ключевые поля: `check_group`, `artifact_type`, `artifact_id`, `status`, `severity`, `report_path`, `summary_json`, `metrics_json`, `violations_json`.

`CRITICAL` используется для leakage нарушений, которые могут сделать model-ready artifact непригодным.

##### Traceability chain

Полная цепочка для model-ready artifact:

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

Если любой обязательный link отсутствует, `TraceabilityService` возвращает ошибку, а readiness check помечает traceability как `FAILED`.

---

### Источник: `docs/ru/normalization/parser_strategy.md`

[Открыть исходный файл](ru/normalization/parser_strategy.md)

#### Стратегия parser registry и выбора parser

Parser strategy состоит из трех частей:

1. `parser_registry_seed.json` описывает поддерживаемые parser groups.
2. `ParserRegistrySeeder` разворачивает groups в строки `parser_registry`.
3. `ParserResolver` выбирает активный parser для конкретного `dataset_files` по `branch`, `role`, `source_format`.

##### Seed registry

Файл:

```text
scripts/stage_two/parser_registry/parser_registry_seed.json
```

Seed загружается командой:

```bash
python manage.py stage-two seed-parser-registry
```

Seeder проверяет, что `parser_module` и `parser_class` импортируются. Если класс отсутствует или не наследуется от `BaseParser`, entry может быть сохранен как inactive с diagnostic metadata в `config_json.class_validation`.

##### Как выбирается parser

`ParserResolver` ищет active entries:

```text
branch == dataset_file.branch
source_format == dataset_file.source_format
supported_role == dataset_file.role OR supported_role IS NULL
is_active == true
```

Затем сортирует по `priority`, потом `id`. Role-specific entry имеет преимущество только через порядок/priority; универсальная запись с `supported_role = NULL` подходит для всех ролей.

Если parser не найден:

- `resolve_or_mark_unsupported()` переводит файл в `UNSUPPORTED_FORMAT`;
- `normalize-format` возвращает status `UNSUPPORTED_FORMAT` для выбранного bucket;
- parser run не должен имитировать успешную нормализацию.

##### Реализованные parser groups

###### DNS

| Parser class | Source formats | Roles | Модуль |
| --- | --- | --- | --- |
| `DnsCsvParser` | `csv` | all active roles | `scripts.stage_two.parsers.dns` |
| `DnsPcapCsvParser` | `pcap.csv` | all active roles | `scripts.stage_two.parsers.dns` |
| `DnsTxtDomainListParser` | `txt` | `VALIDATION` | `scripts.stage_two.parsers.dns` |
| `DnsPacketCaptureParser` | `cap`, `pcap`, `pcapng` | all active roles | `scripts.stage_two.parsers.dns` |

###### Host

| Parser class | Source formats | Roles | Модуль |
| --- | --- | --- | --- |
| `HostCsvParser` | `csv` | all active roles | `scripts.stage_two.parsers.host` |
| `HostJsonLinesParser` | `json`, `json-1` | all active roles | `scripts.stage_two.parsers.host` |
| `HostLineLogParser` | `auth.log`, `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `info`, `journal`, `journal~`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `uptime.log` | all active roles | `scripts.stage_two.parsers.host` |
| `HostSyscallTraceParser` | `txt`, `sc`, `ghc` | all active roles | `scripts.stage_two.parsers.host` |
| `HostXmlParser` | `xml` | all active roles | `scripts.stage_two.parsers.host` |
| `HostNetflowParser` | `netflow_day`, `netflow_ids`, `wls_day` | all active roles | `scripts.stage_two.parsers.host` |
| `HostPacketCaptureParser` | `cap`, `pcap`, `pcapng` | `TRAIN`, `VALIDATION` | `scripts.stage_two.parsers.host` |
| `HostBsonSandboxParser` | `bson` | `TEST` | `scripts.stage_two.parsers.host` |

Metricbeat-like логи обрабатываются через существующие host parser modules/helpers; отдельной active seed group с именем `HostMetricbeatParser` в текущем registry seed нет.

##### Lifecycle statuses parser

| Уровень | Status | Значение |
| --- | --- | --- |
| parser run | `SUCCESS` | Parser completed and emitted events without failed rows. |
| parser run | `PARTIAL_SUCCESS` | Parser emitted events, but some rows/records failed. |
| parser run | `FAILED` | Parser failed for the file. |
| parser run | `SKIPPED` | File intentionally skipped. |
| dataset file | `PARSED` | Файл успешно нормализован. |
| dataset file | `PARTIALLY_PARSED` | Есть normalized events, но были ошибки. |
| dataset file | `FAILED` | Нормализация не удалась. |
| dataset file | `SKIPPED` | Файл пропущен по parser/result policy. |
| dataset file | `UNSUPPORTED_FORMAT` | Для `branch/role/source_format` нет parser. |

Stage One analysis statuses вроде `READY_FOR_FEATURE_EXTRACTION`, `NEEDS_CUSTOM_PARSER`, `PARTIALLY_SUPPORTED`, `BROKEN_OR_EMPTY` используются как input guidance для parser strategy, но Stage Two catalog lifecycle использует DB statuses выше.

##### Контракт ParserResult

Parser возвращает `ParserResult`:

- `events`: список normalized event rows;
- counters: rows read/parsed/failed, events emitted;
- errors/warnings/metadata;
- optional `status_override`: `EMPTY_FILE`, `FAILED`, `SKIPPED`, `UNSUPPORTED_FORMAT`.

`ParserResult.status_decision` преобразует результат в parser run/file statuses. Empty output без явной причины не должен маскироваться как успешный benign dataset.

##### Ошибки и граничные случаи

| Сценарий | Поведение |
| --- | --- |
| Missing parser class | Seed entry становится inactive или получает validation diagnostics. |
| Parser не найден | `dataset_files.status = UNSUPPORTED_FORMAT`. |
| Binary PCAP/PCAPNG большой | Использовать `--packet-mode packet-summary` или `sample`; учитывать performance risk. |
| TEST labels в имени файла | Filename hints отключены для `TEST`. |
| Mixed schema CSV/JSON | Parser должен сохранять неизвестные поля в JSON payload и фиксировать warnings. |
| Partially corrupt file | Допустим `PARTIAL_SUCCESS`/`PARTIALLY_PARSED`, counters должны показывать failed rows. |

##### Проверка покрытия

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage dns
python manage.py stage-two parser-coverage host
```

Проверка сравнивает зарегистрированные `dataset_files` combinations с `parser_registry`. Ее нужно запускать после `catalog-ingest` и `seed-parser-registry`.

---

### Источник: `docs/ru/normalization/parser_development_guide.md`

[Открыть исходный файл](ru/normalization/parser_development_guide.md)

#### Руководство добавления parser implementation

Этот документ описывает минимальный контракт нового parser в Stage Two. Новый parser должен быть безопасен для raw data, не смешивать роли и сохранять traceability.

##### Где менять код

| Задача | Файл/директория |
| --- | --- |
| Parser class | `scripts/stage_two/parsers/*.py` |
| Shared helpers | `scripts/stage_two/parsers/common.py`, `csv_utils.py`, `json_utils.py`, `input_reader.py` |
| Registry entry | `scripts/stage_two/parser_registry/parser_registry_seed.json` |
| Schema contract | `schemas/normalized/normalized_event_v1.json` или новая schema version |
| Parser tests/smoke | `scripts/stage_two/parser_smoke.py`, `parser_input_smoke.py`, project tests if present |
| Документация | `docs/ru/normalization/parser_strategy.md`, этот файл, при необходимости schema docs |

##### Минимальный контракт parser

Parser class должен:

1. наследоваться от `BaseParser`;
2. принимать `ParserContext`;
3. возвращать `ParserResult`;
4. заполнять обязательные normalized fields;
5. не изменять raw файл;
6. сохранять `event_index` или другой порядок, если timestamp отсутствует;
7. использовать `LabelResolver`, а не назначать benign по умолчанию;
8. сохранять неизвестные raw values в `raw_fields_json`/`metadata_json`, а не терять их.

Обязательные поля перечислены в [normalized_event_schema.md](ru/normalization/normalized_event_schema.md).

##### Шаблон решения

```python
from pathlib import Path

from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import build_timestamp_fields
from scripts.stage_two.parsers.input_reader import UniversalInputReader


class MyParser(BaseParser):
    parser_name = "my_parser"
    parser_version = "v1"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        events: list[dict[str, object]] = []
        errors: list[str] = []

        reader = UniversalInputReader(path)
        with reader.open("json_lines") as records:
            for event_index, raw_record in enumerate(records):
                try:
                    timestamp_fields = build_timestamp_fields(
                        raw_record.get("timestamp"),
                        event_index=event_index,
                    )
                    labels = self.label_resolver.resolve(raw_record, context)
                    events.append(self.base_event(
                        context,
                        event_index=event_index,
                        **timestamp_fields,
                        **labels,
                        event_type="my_event",
                        entity_type="host",
                        modality="host_event",
                        raw_fields_json=raw_record,
                    ))
                except Exception as exc:
                    errors.append(f"event_index={event_index}: {exc}")

        return ParserResult(
            events=events,
            rows_read=len(events) + len(errors),
            rows_parsed=len(events),
            rows_failed=len(errors),
            error_samples=errors,
        )
```

В реальном parser используйте тот reader mode, который соответствует формату (`csv_rows`, `json_lines`, `lines`, `binary`, `packet_bytes`, `bson_stream`). Не добавляйте псевдополя в normalized output без обновления schema contract.

##### Запись в registry

После добавления class нужно добавить или расширить parser group в:

```text
scripts/stage_two/parser_registry/parser_registry_seed.json
```

Минимальные поля:

```json
{
  "parser_name": "my_parser",
  "parser_version": "v1",
  "branch": "host",
  "source_formats": ["my_format"],
  "supported_roles": null,
  "priority": 100,
  "normalized_schema_name": "normalized_event",
  "normalized_schema_version": "v1",
  "parser_module": "scripts.stage_two.parsers.host",
  "parser_class": "MyParser"
}
```

`supported_roles = null` означает все активные роли. Если parser допустим только для `TEST` или только для `TRAIN/VALIDATION`, задайте список явно. Например `HostBsonSandboxParser` ограничен `TEST`, а `HostPacketCaptureParser` - `TRAIN`/`VALIDATION`.

##### Обработка labels

Parser не должен самостоятельно назначать `label_binary = 0` при отсутствии label. Используйте `LabelResolver`:

- explicit embedded/external labels дают `explicit_label` или configured status;
- weak/inferred labels должны иметь confidence/source;
- conflicting labels должны фиксироваться как `conflicting_label`;
- для `TEST` filename/embedded heuristics отключены.

См. [label_resolver.md](ru/normalization/label_resolver.md).

##### Обработка timestamp

Запрещено подставлять `datetime.now()` для отсутствующего timestamp.

Используйте правила:

```text
timestamp present -> timestamp_type = absolute
timestamp missing but event_index present -> timestamp_type = event_order
timestamp missing and no ordering -> timestamp_type = missing
```

##### Обработка ошибок

| Ошибка | Как фиксировать |
| --- | --- |
| Битая строка | Увеличить failed counter, добавить sample в errors, продолжить если возможно. |
| Empty file | Вернуть status override `EMPTY_FILE` или `SKIPPED`, не создавать fake benign events. |
| Unsupported subformat | Вернуть `UNSUPPORTED_FORMAT` или error metadata, если parser не может безопасно читать файл. |
| Schema drift | Сохранить raw payload в JSON fields и добавить warning. |
| Large binary file | Использовать packet summary/sample режимы; не загружать весь файл в память без необходимости. |

##### Проверки после добавления parser

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --dry-run
python manage.py stage-two normalize-format --branch <branch> --role <ROLE> --format <format> --limit 10
python manage.py stage-two run-duckdb-checks
```

Если parser влияет на labels или model-ready downstream, дополнительно:

```bash
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

##### Документация, которую нужно обновить

- `parser_strategy.md` - список parser classes/source formats.
- `normalized_event_schema.md` - если добавлены новые normalized fields или новая schema version.
- `label_resolver.md` - если появились новые label fields/rules.
- `data_quality_checks.md` - если нужен новый quality check.
- `performance_tuning.md` - если parser требует специальных runtime limits.

---

### Источник: `docs/ru/normalization/normalized_event_schema.md`

[Открыть исходный файл](ru/normalization/normalized_event_schema.md)

#### Схема normalized event

Normalized event schema хранится в:

```text
schemas/normalized/normalized_event_v1.json
```

Это JSON contract с `schema_name = "normalized_event"`, `schema_version = "v1"`, `layer = "normalized"` и массивом `fields`. Parser implementations должны выдавать rows, совместимые с этим контрактом.

##### Обязательные поля parser output

Базовый parser contract в `scripts/stage_two/parsers/base.py` требует поля:

```text
event_uid
dataset_name
dataset_role
branch
source_format
source_file_path
parser_name
parser_version
schema_name
schema_version
timestamp_type
entity_type
event_type
modality
label_source
label_status
created_at
```

Дополнительные поля из JSON schema могут быть nullable, но parser должен сохранять traceability и label/timestamp null policy.

##### Traceability поля

| Поле | Назначение |
| --- | --- |
| `event_uid` | Уникальный идентификатор normalized event. |
| `dataset_name` | Имя dataset из catalog/source context. |
| `dataset_role` | `TRAIN`, `VALIDATION` или `TEST`. |
| `branch` | `dns`, `host`, `network`, `hybrid`. |
| `source_format` | Формат raw файла. |
| `source_file_path` | Путь к исходному файлу. |
| `source_file_hash` | SHA-256 raw файла, если доступен из catalog. |
| `parser_run_id` | ID parser run, связывает event с `parser_runs`. |
| `parser_name`, `parser_version` | Parser implementation и версия. |
| `schema_name`, `schema_version` | Версия normalized schema. |
| `event_index` | Порядковый номер события внутри файла, если доступен. |

Traceability поля нельзя удалять из normalized artifacts. Для model-ready `X` они считаются leakage/source columns и должны быть исключены из признаков.

##### Timestamp policy

| Поле | Правило |
| --- | --- |
| `timestamp` | Может быть `null`. |
| `timestamp_type` | Одно из `absolute`, `relative`, `event_order`, `missing`. |
| `event_index` | Используется для сохранения порядка, когда абсолютного времени нет. |

Если timestamp отсутствует, нельзя подставлять текущее время. Правильные варианты:

- `timestamp = null`, `timestamp_type = "event_order"`, если есть надежный `event_index`;
- `timestamp = null`, `timestamp_type = "missing"`, если нет времени и порядка.

`build_timestamp_fields()` в `scripts/stage_two/parsers/common.py` реализует это правило: timestamp дает `absolute`, event index без timestamp дает `event_order`, отсутствие обоих дает `missing`.

##### DNS поля

DNS parsers заполняют поля, связанные с DNS/network context, если они есть в source:

- `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`;
- `query_domain`, `qtype`, `qclass`, `rcode`, `ttl`;
- DNS-specific values внутри `features_json` или `raw_fields_json`, если исходная схема не совпадает напрямую с normalized fields.

DNS packet captures могут давать summary-level events в зависимости от `--packet-mode`.

##### Host поля

Host parsers используют поля, связанные с host telemetry:

- process: `process_id`, `process_name`, parent process fields;
- file/path: `path`, file action fields;
- syscall/log: `sys_call`, `event_id`, `event_type`;
- metrics/log payload, если source формат логовый или metricbeat-like.

Для нестандартных строковых логов часть значений сохраняется в `raw_fields_json`, а normalized columns заполняются только когда значение можно извлечь без выдумывания.

##### Network/hybrid поля

`network` и `hybrid` branches есть в schema/catalog constants, но текущий normalization runner поддерживает только `dns` и `host`. Network/hybrid fields могут использоваться контрактами будущих parsers, но не должны описываться как полностью реализованный normalization pipeline.

##### Labels

Unlabeled event должен иметь:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Отсутствующий label не равен benign. Для `TEST` filename/embedded heuristics отключены `LabelResolver.label_hints_allowed()`, чтобы не вносить leakage через имя файла или поля, которые не являются explicit external ground truth.

##### JSON поля

| Поле | Назначение |
| --- | --- |
| `features_json` | Parser-level extracted attributes, которые еще не являются model-ready X features. |
| `raw_fields_json` | Исходные поля или фрагменты raw record для audit/debug. |
| `metadata_json` | Parser/file metadata, warnings, confidence, дополнительные counters. |

`ParquetArtifactWriter` сериализует поля с суффиксом `_json` в deterministic JSON strings перед записью Parquet.

##### Граничные случаи

| Сценарий | Ожидаемое поведение |
| --- | --- |
| Empty file | Parser result может привести к `EMPTY_FILE`/`SKIPPED`, artifact не обязан создаваться. |
| Частично битые строки | Допустим `PARTIAL_SUCCESS`/`PARTIALLY_PARSED`, ошибки фиксируются в parser run counters/error samples. |
| Неизвестный source format | Файл получает `UNSUPPORTED_FORMAT`, если resolver не нашел parser. |
| Schema drift | Parser должен сохранять неизвестные raw values в `raw_fields_json`/`metadata_json`, а не расширять model-ready X без schema review. |

---

### Источник: `docs/ru/normalization/label_resolver.md`

[Открыть исходный файл](ru/normalization/label_resolver.md)

#### Разрешение labels

`LabelResolver` находится в:

```text
scripts/stage_two/labels/resolver.py
```

Он приводит labels из разных источников к canonical normalized fields и защищает pipeline от опасного предположения "нет label = benign".

##### Canonical label fields

| Поле | Значение |
| --- | --- |
| `label_binary` | `1`, `0` или `null`. |
| `label_family` | Семейство/класс атаки, если известно. |
| `label_subtype` | Более точный subtype, если известен. |
| `label_source` | `embedded_column`, `external_file`, `scenario_metadata`, `filename`, `ids_alert`, `none` и т.п. |
| `label_status` | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label`. |
| `label_confidence` | Число confidence, если применимо. |
| `label_mapping_rule_id` | ID rule из catalog/config, если label получен правилом. |

Unlabeled output:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

##### Источники labels

| Источник | Приоритет | Комментарий |
| --- | --- | --- |
| Embedded column | 0 | Поля вроде `label_binary`, `label`, `target`, `class`, `is_attack`, `malicious`, `attack_cat`. |
| External/ground truth rule | 1 | Rule из catalog/config, если он явно матчится. |
| Scenario metadata | 2 | Metadata контекст dataset/scenario. |
| Filename | 3 | Weak/inferred hint из имени файла; запрещен для `TEST`. |
| IDS alert | 4 | Alert-derived weak signal. |
| None | 99 | Нет label. |

Точные поля embedded labels перечислены в `EMBEDDED_LABEL_FIELDS` в `resolver.py`.

##### Политика TEST

`LabelResolver.label_hints_allowed()` возвращает `False` для `TEST`. Это означает:

- filename heuristic нельзя использовать для label inference в `TEST`;
- embedded/IDS hints, которые являются эвристикой, не должны превращать `TEST` в training signal;
- `TEST` не используется для threshold tuning, feature selection или preprocessing fit.

Explicit external ground truth rules допустимы только если они не являются filename heuristic и явно заданы как label source. Если label отсутствует, событие остается unlabeled.

##### Конфликтующие labels

Если разные источники дают несовместимые canonical labels, результат должен фиксироваться как `conflicting_label`, а не silently выбирать benign/malicious. Такой случай должен попадать в metadata/errors и далее в quality review.

##### Использование в parser

Parser должен передавать raw record и context в resolver и включать результат в normalized event:

```python
labels = self.label_resolver.resolve(record, context)
event.update(labels)
```

Если parser читает source, где label отсутствует, он не должен создавать `label_binary = 0`. Правильный output - unlabeled contract выше.

##### Labels и model-ready artifacts

Labels не входят в X features. Они должны храниться отдельно:

- в normalized events как label metadata;
- в feature/model-ready metadata как label distribution;
- в model-ready `y` artifact, если downstream stage создает labels table.

Для model-ready `X` поля `label_binary`, `label_family`, `label_subtype`, `label_source`, `label_status`, `label_confidence`, `label_mapping_rule_id` и другие label/source columns запрещены.

---

### Источник: `docs/ru/normalization/parquet_duckdb_artifacts.md`

[Открыть исходный файл](ru/normalization/parquet_duckdb_artifacts.md)

#### Parquet и DuckDB артефакты

Stage Two хранит большие таблицы в Parquet и использует DuckDB для аналитических SQL-проверок поверх этих файлов. PostgreSQL Catalog хранит только metadata: paths, row counts, hashes, schema versions, statuses и связи.

##### Parquet writer

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

##### Пути normalized artifacts

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

##### Пути feature artifacts

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

##### Пути model-ready artifacts

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

##### DuckDB service

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

##### DuckDB checks

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

##### Ограничения

- DuckDB читает уже записанные Parquet files; он не заменяет PostgreSQL Catalog.
- Feature/model-ready paths могут существовать только после вызова соответствующих writer/registry services; CLI build step для них сейчас не реализован.
- Перемещение Parquet files без обновления catalog ломает traceability.
- `TRAIN`, `VALIDATION`, `TEST` должны оставаться раздельными на уровне path, catalog metadata и downstream artifacts.

---

### Источник: `docs/ru/normalization/data_quality_checks.md`

[Открыть исходный файл](ru/normalization/data_quality_checks.md)

#### Проверки качества данных

Stage Two использует два уровня проверок:

1. DuckDB analytics checks поверх Parquet views.
2. `DataQualityChecker`/`LeakageChecker` с регистрацией результатов в `data_quality_reports`.

##### DuckDB analytics

Команда:

```bash
python manage.py stage-two run-duckdb-checks
```

Код:

```text
scripts/stage_two/duckdb/service.py
```

Проверяет:

- созданы ли views `normalized_all`, `features_all`, `model_ready_all`;
- row counts по Parquet layers;
- наличие required columns;
- split contamination;
- schema mismatch.

Report:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

После регистрации в catalog создается запись `data_quality_reports` с `check_group` для DuckDB/quality diagnostics.

##### DataQualityChecker

Код:

```text
scripts/stage_two/quality/checkers.py
```

`DataQualityChecker` читает DuckDB views и проверяет:

| Проверка | Цель |
| --- | --- |
| Required columns | Контрактные колонки присутствуют в views. |
| Null counts | Видимость пустых значений в критичных columns. |
| Duplicate keys | Дубликаты ключевых event/sample identifiers. |
| Role domain | Значения role/dataset_role ограничены `TRAIN`, `VALIDATION`, `TEST`. |
| Branch domain | Значения branch ограничены catalog constants. |

Reports пишутся в RU/EN report roots и могут регистрироваться через `DataQualityRepository`.

##### Уровни severity

| Severity | Значение |
| --- | --- |
| `INFO` | Диагностическая информация. |
| `WARNING` | Нежелательное состояние, которое не всегда блокирует pipeline. |
| `ERROR` | Нарушение контракта или качества данных. |
| `CRITICAL` | Нарушение, которое может привести к leakage, смешиванию splits или недостоверному model-ready artifact. |

##### Связь с leakage checks

`LeakageChecker` находится в том же модуле, но описан отдельно в [data_leakage_prevention.md](ru/normalization/data_leakage_prevention.md). Его CRITICAL results также регистрируются в `data_quality_reports`, обычно с `check_group = "leakage"`.

##### Readiness check

```bash
python -m scripts.stage_two.readiness_check
```

Readiness проверяет, что:

- миграции применены;
- storage paths существуют;
- catalog содержит datasets/files/parser_registry/schema_versions/artifacts/reports;
- parser coverage не имеет uncovered combinations;
- normalized artifacts есть и не failed;
- feature/model-ready artifacts связаны с upstream artifacts;
- quality/leakage reports существуют;
- traceability chain восстанавливается;
- raw file hashes совпадают с catalog.

Readiness report сохраняется в:

```text
reports/en/stage-two/stage_two_readiness_report.md
reports/ru/stage-two/stage_two_readiness_report.md
reports/en/stage-two/stage_two_readiness_report.json
```

##### Что считается блокирующим

Блокирующие сценарии:

- `TEST` найден в preprocessing fit/training context;
- label/source fields присутствуют в model-ready `X`;
- отсутствует обязательная traceability связь;
- raw file hash не совпадает с catalog;
- parser coverage отсутствует для files, которые должны нормализоваться;
- role contamination между `TRAIN`, `VALIDATION`, `TEST`.

Такие нарушения нужно исправлять до использования artifacts в ML experiments.

---

### Источник: `docs/ru/normalization/data_leakage_prevention.md`

[Открыть исходный файл](ru/normalization/data_leakage_prevention.md)

#### Предотвращение data leakage

Leakage prevention в Stage Two опирается на contract-level запреты, catalog traceability и runtime checks. Главная цель: labels, source identifiers и split metadata не должны попадать в model-ready `X`.

##### Неприкосновенные правила

1. `TEST` не используется для обучения, fit preprocessing, fit scaler, fit encoder, threshold tuning или feature selection.
2. `TRAIN`, `VALIDATION`, `TEST` не смешиваются в одном model-ready artifact.
3. Labels не являются обычными input features.
4. Filename heuristic для `TEST` labels запрещен.
5. Отсутствующий label не означает benign.
6. Traceability fields сохраняются в catalog/metadata, но исключаются из `X`.

##### Запрещенные X columns

Запрещенные columns берутся из feature/model-ready contracts:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
label
labels
target
class
is_attack
is_malicious
malicious
attack
attack_cat
attack_category
attack_subcat
is_executing_exploit
exploit
ground_truth
ground_truth_label
dataset_id
dataset_name
dataset_role
role
branch
source_format
source_file
source_file_name
source_file_path
source_file_hash
source_normalized_path
source_event_uid_refs
parser_run_id
parser_name
parser_version
schema_name
schema_version
normalized_artifact_id
feature_group
feature_schema_name
feature_schema_version
event_uid
sample_uid
entity_type
entity_id
window_start
window_end
window_size_seconds
window_step_seconds
scenario_name
raw_fields_json
metadata_json
created_at
```

`ModelReadyRegistryService.write_table_artifact()` вызывает `validate_x_columns()` для `data_type = "X"` и отклоняет rows, если в них есть запрещенные поля.

##### LeakageChecker

Команда:

```bash
python manage.py stage-two run-leakage-checks
```

Код:

```text
scripts/stage_two/quality/checkers.py
```

Проверки:

| Проверка | Что ловит |
| --- | --- |
| `x_forbidden_columns` | Label/source/traceability columns внутри model-ready `X`. |
| `test_absent_from_train` | Использование `TEST` в training context. |
| `preprocessing_fit_only_train` | Preprocessing artifact fitted на роли, отличной от `TRAIN`. |

CRITICAL нарушения регистрируются в `data_quality_reports` и должны блокировать использование artifact.

##### Labels

Label fields могут присутствовать в normalized events для audit и в model-ready `y`, но не в `X`. События без label остаются unlabeled:

```json
{
  "label_binary": null,
  "label_source": "none",
  "label_status": "unlabeled"
}
```

См. [label_resolver.md](ru/normalization/label_resolver.md).

##### Traceability без leakage

Traceability chain обязателен:

```text
raw -> normalized -> features -> model-ready
```

Но traceability identifiers (`event_uid`, `sample_uid`, paths, hashes, parser IDs) не должны становиться признаками. Они должны храниться:

- в PostgreSQL Catalog;
- в artifact metadata;
- в non-X columns, исключенных из training matrix.

##### Типовые ошибки

| Ошибка | Последствие | Исправление |
| --- | --- | --- |
| `label_binary` попал в X | Модель обучается на ответе. | Пересобрать X после exclusion contract. |
| `source_file_path` попал в X | Модель может выучить dataset/source identity. | Удалить source fields из feature selection. |
| `TEST` использован для scaler fit | Метрики становятся завышенными. | Fit только на `TRAIN`, transform для `VALIDATION`/`TEST`. |
| Unlabeled заменен на benign | Искажение labels. | Сохранять `label_binary = null`, `label_status = unlabeled`. |
| Filename heuristic для TEST | Leakage из имени файла. | Отключить heuristic, использовать только explicit ground truth. |

---

### Источник: `docs/ru/normalization/traceability.md`

[Открыть исходный файл](ru/normalization/traceability.md)

#### Traceability и lineage

Traceability связывает model-ready artifact с исходным raw file через PostgreSQL Catalog и Parquet metadata. Цепочка нужна для audit, воспроизводимости, поиска leakage и проверки, что raw files не изменялись.

##### Реализация

Код:

```text
scripts/stage_two/traceability/service.py
```

CLI:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Числовой аргумент ищется как `model_ready_artifacts.id`, строковый - как `model_ready_artifacts.artifact_path`.

##### Обязательная цепочка

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

Если link отсутствует, `TraceabilityService` выбрасывает `TraceabilityError`. Readiness check считает это `FAILED`.

##### Что возвращает service

Trace chain включает metadata блоки:

- `model_ready_artifact`;
- `feature_artifact`;
- `normalized_artifact`;
- `parser_run`;
- `dataset_file`;
- `dataset`.

Этого достаточно, чтобы ответить:

- из какого raw файла получен artifact;
- каким parser и schema version он обработан;
- где лежит normalized Parquet;
- из какого feature artifact собран model-ready artifact;
- какая role/branch использовалась на каждом уровне.

##### Правила сохранения traceability

1. `normalized_artifacts.parser_run_id` должен ссылаться на реальный `parser_runs.id`.
2. `parser_runs.file_id` должен ссылаться на `dataset_files.id`.
3. `feature_artifacts.normalized_artifact_id` должен быть заполнен для production artifacts.
4. `model_ready_artifacts.feature_artifact_id` должен быть заполнен для traceable model-ready artifacts.
5. Raw file hash в `dataset_files.file_hash_sha256` должен совпадать с текущим файлом при readiness check.

##### Traceability и leakage

Traceability fields нельзя удалять из catalog, но нельзя включать в model-ready `X`. Поля paths, hashes, IDs и raw metadata могут идентифицировать dataset/source и создавать leakage. Они должны оставаться в catalog/metadata или быть исключены через `x_excluded_columns`.

##### Проверка

```bash
python manage.py stage-two trace-artifact 123
python -m scripts.stage_two.readiness_check
```

`readiness_check` дополнительно проверяет один последний traceable model-ready artifact и raw file hashes.

---

### Источник: `docs/ru/normalization/final_summary_template.md`

[Открыть исходный файл](ru/normalization/final_summary_template.md)

#### Шаблон итоговой сводки Stage Two normalization

Используйте шаблон после изменения parser/normalization pipeline или после полного запуска Stage Two.

##### Область запуска

- Branches:
- Roles:
- Source formats:
- Storage root:
- Catalog DB:
- Code revision:

##### Команды

```bash
python manage.py stage-two bootstrap-storage
alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --apply
python manage.py stage-two normalize-format --branch <branch> --role <ROLE> --format <format> --limit <N>
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

##### Сводка catalog

| Table | Count | Notes |
| --- | ---: | --- |
| `datasets` |  |  |
| `ingestion_runs` |  |  |
| `dataset_files` |  |  |
| `parser_registry` |  |  |
| `parser_runs` |  |  |
| `normalized_artifacts` |  |  |
| `feature_artifacts` |  |  |
| `model_ready_artifacts` |  |  |
| `data_quality_reports` |  |  |

##### Parser coverage

| Branch | Role | Source format | Parser | Status | Notes |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

##### Результаты normalization

| Branch | Role | Source format | Files | Parsed | Partial | Failed | Unsupported |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
|  |  |  |  |  |  |  |  |

##### Quality и leakage

| Check group | Status | Severity | Report path | Notes |
| --- | --- | --- | --- | --- |
| DuckDB analytics |  |  |  |  |
| Data quality |  |  |  |  |
| Leakage |  |  |  |  |
| Readiness |  |  |  |  |

##### Пример traceability

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

Artifact checked:

- model_ready_artifact:
- feature_artifact:
- normalized_artifact:
- parser_run:
- dataset_file:
- dataset:

##### Ограничения и follow-up

- Unsupported formats:
- Parser gaps:
- Label risks:
- Timestamp risks:
- Риски больших файлов:
- Schema drift:
- Требуемые следующие действия:

---

### Источник: `docs/ru/normalization/host_validation_wls_day_exclusion.md`

[Открыть исходный файл](ru/normalization/host_validation_wls_day_exclusion.md)

#### Исключение Host VALIDATION wls_day

Raw bucket `host/VALIDATION/wls_day` исключен из активной Stage Two обработки после того, как большие JSONL-файлы были разделены и зарегистрированы как chunks.

Активная обработка должна использовать только:

```text
chunked/host/VALIDATION/wls_day/...
```

Не удаляйте raw-файлы физически без отдельного решения оператора. Traceability по исходным файлам, parser runs и уже созданным artifacts должна сохраняться. Невалидные normalized artifacts, созданные из исходных больших файлов, должны оставаться зарегистрированными, но не должны иметь `SUCCESS`.

Ожидаемое состояние catalog:

- исходные raw-файлы: `dataset_files.status = SKIPPED`
- parser runs исходных файлов: `parser_runs.status = SKIPPED`
- normalized artifacts от parser runs исходных файлов: `normalized_artifacts.status = SKIPPED`
- chunked-файлы: остаются доступными как `READY_FOR_PARSING` или `PARSED`

Scanner и operational selectors не должны повторно активировать raw bucket. Роли `TRAIN`, `VALIDATION` и `TEST` не смешиваются; это исключение относится только к Host `VALIDATION` `wls_day`.

---

## Документация по коду

### Источник: `docs/ru/code-documentation/README.md`

[Открыть исходный файл](ru/code-documentation/README.md)

#### Документация по коду проекта

Этот раздел описывает кодовую базу `Proposal`: инвентаризацию и анализ Stage One, pipeline нормализации Stage Two, каталог PostgreSQL, контракты схем, стратегию парсеров, обработку меток, Parquet/DuckDB-артефакты, проверки качества/утечек и точки расширения.

Документация нужна разработчику, который подключается к проекту без предварительного чтения всего кода. Она фиксирует не только назначение файлов, но и контракты данных, порядок запуска, статусы, ограничения и зоны риска.

##### Карта документов

| Документ | Назначение |
|---|---|
| [cli_and_routing.md](ru/code-documentation/cli_and_routing.md) | `manage.py`, слой маршрутизации, команды Stage One/Stage Two, порядок запуска |
| [stage_one_handlers.md](ru/code-documentation/stage_one_handlers.md) | handlers Stage One: анализ, фильтрация, сортировка, экспорт путей, анализ содержимого, JSON |
| [stage_two_overview.md](ru/code-documentation/stage_two_overview.md) | pipeline Stage Two: storage, ingestion, registry, normalization, checks |
| [storage_architecture.md](ru/code-documentation/storage_architecture.md) | `PATH_DATA_STORAGE`, обязательные директории, пути артефактов |
| [postgresql_catalog.md](ru/code-documentation/postgresql_catalog.md) | таблицы PostgreSQL catalog и цепочка трассируемости |
| [sqlalchemy_layer.md](ru/code-documentation/sqlalchemy_layer.md) | config/session/models/repositories/migrations/smoke check |
| [normalized_event_schema.md](ru/code-documentation/normalized_event_schema.md) | `normalized_event_v1`, поля, timestamp, labels, traceability |
| [parser_strategy.md](ru/code-documentation/parser_strategy.md) | parser registry, resolver, parser classes, статусы parser runs |
| [label_resolver.md](ru/code-documentation/label_resolver.md) | источники labels, ограничения TEST, конфликтные labels |
| [parquet_and_duckdb.md](ru/code-documentation/parquet_and_duckdb.md) | Parquet writer, пути, compression, DuckDB views/checks |
| [data_quality_checks.md](ru/code-documentation/data_quality_checks.md) | DataQualityChecker, DuckDB analytics, отчеты |
| [data_leakage_prevention.md](ru/code-documentation/data_leakage_prevention.md) | запрещенные X-колонки, инварианты TRAIN/VALIDATION/TEST |
| [traceability.md](ru/code-documentation/traceability.md) | цепочка raw -> normalized -> features -> model-ready |
| [dataset_contracts.md](ru/code-documentation/dataset_contracts.md) | DNS/Host TRAIN/VALIDATION/TEST форматы, количества, labels, потребности parser |
| [extension_points.md](ru/code-documentation/extension_points.md) | как добавлять handlers, parsers, schemas, labels, checks, stages |
| [risks_and_technical_debt.md](ru/code-documentation/risks_and_technical_debt.md) | известные ограничения, parser gaps, риски leakage/timestamp/large files |

##### Рекомендуемый порядок чтения

1. [cli_and_routing.md](ru/code-documentation/cli_and_routing.md)
2. [stage_one_handlers.md](ru/code-documentation/stage_one_handlers.md)
3. [stage_two_overview.md](ru/code-documentation/stage_two_overview.md)
4. [postgresql_catalog.md](ru/code-documentation/postgresql_catalog.md)
5. [normalized_event_schema.md](ru/code-documentation/normalized_event_schema.md)
6. [parser_strategy.md](ru/code-documentation/parser_strategy.md)
7. [label_resolver.md](ru/code-documentation/label_resolver.md)
8. [data_leakage_prevention.md](ru/code-documentation/data_leakage_prevention.md)
9. [dataset_contracts.md](ru/code-documentation/dataset_contracts.md)
10. [risks_and_technical_debt.md](ru/code-documentation/risks_and_technical_debt.md)

##### Stage One

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

##### Stage Two

Stage Two создает storage-структуру, регистрирует raw-файлы в PostgreSQL catalog, seed-ит metadata схем и парсеров, выбирает parser, нормализует события в Parquet, пишет parser reports, выполняет DuckDB checks, quality/leakage checks и обеспечивает трассируемость raw -> normalized -> features -> model-ready.

Фактические компоненты находятся в `scripts/stage_two`, `scripts/db`, `schemas`.

Сверка с текущим кодом от 2026-07-04:

- `router_stage_two()` поддерживает `bootstrap-storage`, `catalog-ingest`, `seed-parser-registry`, `parser-coverage`, `mark-ready`, `normalize-format`, `normalize-all`, `benchmark-normalization`, `split-large-files`, `normalize-dns`, `normalize-host`, `run-duckdb-checks`, `run-leakage-checks` и `trace-artifact`.
- `config.manage_commands` является только fallback-списком для вывода в консоль и не полон для новых Stage Two команд.
- `normalize-format` и `benchmark-normalization` перед запуском применяют resource profiles и format-specific runtime policy; `normalize-all` получает общие runtime options, но не применяет per-format policy на уровне CLI route.
- В `features/` и `model_ready/` есть contracts и registry/writer services, но полный training/evaluation pipeline через `manage.py` не опубликован.

##### Ключевые инварианты

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

##### Основные CLI-команды

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

Подробные аргументы и порядок запуска описаны в [cli_and_routing.md](ru/code-documentation/cli_and_routing.md).

---

### Источник: `docs/ru/code-documentation/cli_and_routing.md`

[Открыть исходный файл](ru/code-documentation/cli_and_routing.md)

#### CLI и слой routing

##### Точка входа

Главная точка входа: `manage.py`.

`manage.py` создает `argparse.ArgumentParser` с позиционными аргументами:

| Аргумент | Назначение |
|---|---|
| `module` | верхний routing namespace: `handlers` или `stage-two` |
| `service` | service/action group внутри module |
| `action` | первый action или первый positional argument service-команды |
| `extra_args` | остаток аргументов для Stage Two команд |

Фактическая маршрутизация:

```text
manage.py
  -> scripts.router_script.router_commands(module, service, action, extra_args)
     -> handlers: scripts.handlers.router_handler.router_commands_handlers(service, action)
     -> stage-two: scripts.stage_two.cli.router_stage_two(service, action, extra_args)
```

Если `module` неизвестен, печатается `config.manage_commands`.

Сверка с кодом от 2026-07-04: `config.manage_commands` является fallback-строкой для вывода в консоль и старше текущего Stage Two router. Для Stage Two используйте `scripts/stage_two/cli.py` и этот документ как актуальный список команд.

##### Маршруты Stage One

Файл: `scripts/handlers/router_handler.py`.

| Service | Router | Actions |
|---|---|---|
| `analyze-dataset` | `scripts/handlers/analyze_dataset/router_analyze.py` | `dns-dataset-handler`, `host-dataset-handler` |
| `filter-dataset` | `scripts/handlers/filter_dataset/router_filter.py` | `filter-host-dataset-handler` |
| `sort` | `scripts/handlers/sort/router_sort.py` | `sort-dns-dataset-handler`, `sort-host-dataset-handler` |
| `save-sort` | `scripts/handlers/save_sort/router_save.py` | `save-sort-dns-dataset-handler`, `save-sort-host-dataset-handler` |
| `dns-analyze` | `scripts/handlers/dns_analyze/router_dns.py` | DNS actions по role/format content |
| `host-analyze` | `scripts/handlers/host_analyze/router_host.py` | Host actions по role/format content |

###### Порядок Stage One DNS

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers dns-analyze <action>
```

DNS content actions:

```bash
python manage.py handlers dns-analyze analyze-train-csv-content
python manage.py handlers dns-analyze analyze-train-pcap-content
python manage.py handlers dns-analyze analyze-train-pcap-csv-content
python manage.py handlers dns-analyze analyze-test-csv-content
python manage.py handlers dns-analyze analyze-test-pcap-content
python manage.py handlers dns-analyze analyze-test-pcap-csv-content
python manage.py handlers dns-analyze analyze-validation-pcap-content
python manage.py handlers dns-analyze analyze-validation-txt-content
```

###### Порядок Stage One Host

```bash
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers host-analyze <action>
```

Host content actions включают `analyze-csv-content`, `analyze-auth-log-content`, `analyze-json-content`, `analyze-validation-pcapng-content`, `analyze-test-bson-content`, `analyze-test-wls-day-content` и другие actions из `scripts/handlers/host_analyze/router_host.py`.

##### Маршруты Stage Two

Файл: `scripts/stage_two/cli.py`.

| Команда | Аргументы | Назначение |
|---|---|---|
| `bootstrap-storage` | нет | создать storage tree под `PATH_DATA_STORAGE` |
| `catalog-ingest` | нет | просканировать `PATH_FOLDER_DATASETS_FILTER` и зарегистрировать файлы |
| `seed-parser-registry` | нет | зарегистрировать normalized schema и parser registry seed |
| `parser-coverage` | `[branch]` | показать coverage catalog formats vs active parsers |
| `mark-ready` | flags или fallback | перевести выбранные файлы в `READY_FOR_PARSING` |
| `normalize-format` | flags или fallback | нормализовать одну группу `branch/role/source_format` |
| `normalize-all` | flags или fallback | нормализовать все ready группы внутри branch по очереди |
| `benchmark-normalization` | flags | измерить скорость одного точного bucket `branch/role/source_format` и оценить throughput |
| `split-large-files` | flags | split line-based больших файлов |
| `normalize-dns` | `[limit]` | legacy branch-level normalization для DNS ready files |
| `normalize-host` | `[limit]` | legacy branch-level normalization для Host ready files |
| `run-duckdb-checks` | нет | создать DuckDB views и analytics report |
| `run-leakage-checks` | нет | проверить model-ready leakage и preprocessing fit role |
| `trace-artifact` | `<model_ready_id_or_artifact_path>` | вывести traceability chain |

###### Базовый порядок Stage Two

```bash
python manage.py stage-two bootstrap-storage
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two benchmark-normalization --branch dns --role TRAIN --format csv --limit 1000 --sample-ratio 0.10 --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Порядок из постановки также поддержан для legacy routes:

```bash
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

##### Аргументы Stage Two

`normalize-dns` и `normalize-host` принимают не более одного optional limit. Значение должно быть неотрицательным integer.

`parser-coverage` принимает optional `branch` из `dns`, `host`, `network`, `hybrid`.

`mark-ready`:

```bash
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --retry-failed --apply
python manage.py stage-two mark-ready dry-run:dns:TRAIN:csv
```

`normalize-format`:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format json \
  --limit 100 \
  --workers 1 \
  --batch-size 10000 \
  --max-output-part-rows 50000 \
  --resume \
  --packet-mode packet-summary \
  --hash-output-artifacts
```

Fallback-формат:

```bash
python manage.py stage-two normalize-format host:TRAIN:json:100
```

`normalize-all`:

```bash
python manage.py stage-two normalize-all --branch dns --limit 100 --resume
python manage.py stage-two normalize-all dns:100
```

`split-large-files`:

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

Ограничение: split предназначен для line-based formats. Не применять к binary `cap`, `pcap`, `pcapng`, `bson`.

##### Команды и выходы

| Команда | Основной input | Основной output |
|---|---|---|
| `handlers analyze-dataset dns-dataset-handler` | `PATH_DNS_DATASETS` | `PATH_TEMP_DATA/dns-path-file.json`, `dns-file.json` |
| `handlers analyze-dataset host-dataset-handler` | `PATH_HOST_DATASETS` | `host-path-file.json`, `host-file.json` |
| `handlers filter-dataset filter-host-dataset-handler` | Host JSON inventory | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`, filter log |
| `handlers sort sort-*-dataset-handler` | path/file JSON | sorted tree в `PATH_*_DATASETS_FILTER`, sort summary JSON |
| `handlers save-sort save-sort-*-dataset-handler` | sorted tree | `sort-path-*-file.json`, summary JSON |
| `handlers dns-analyze/host-analyze` | `sort-path-*-file.json` | analysis summary JSON, docs, reports |
| `stage-two catalog-ingest` | `PATH_FOLDER_DATASETS_FILTER` | `datasets`, `ingestion_runs`, `dataset_files` |
| `stage-two seed-parser-registry` | schema JSON + seed JSON | `schema_versions`, `parser_registry` |
| `stage-two normalize-*` | `dataset_files.status=READY_FOR_PARSING` | `parser_runs`, `normalized_artifacts`, Parquet |
| `stage-two run-duckdb-checks` | Parquet layers | JSON quality report, `data_quality_reports` |
| `stage-two run-leakage-checks` | model-ready Parquet + preprocessing catalog | leakage report, `data_quality_reports` |

##### Важные ограничения CLI

- `python manage.py stage-two` без команды печатает `unknown Stage Two command` и legacy-текст `config.manage_commands`; этот вывод не содержит все новые команды и не должен считаться полным help.
- `handlers` routes не принимают произвольные flags; `action` должен совпадать с router case.
- Stage One content analysis падает, если нужный role/format bucket отсутствует в `sort-path-*-file.json`.
- `catalog-ingest` сканирует `PATH_FOLDER_DATASETS_FILTER`, а не raw `PATH_FOLDER_DATASETS`.
- `normalize-format` и `normalize-all` обрабатывают только `READY_FOR_PARSING`.
- `benchmark-normalization` использует те же точные bucket-входы, что и `normalize-format`; actual benchmark принудительно включает resume behavior, если не указан `--dry-run`.
- `normalize-all` группирует по `role/source_format` и сохраняет порядок ролей из `ACTIVE_DATASET_ROLE_VALUES`: `TRAIN`, `VALIDATION`, `TEST`.
- `trace-artifact` работает только для уже зарегистрированных `model_ready_artifacts`.

---

### Источник: `docs/ru/code-documentation/stage_one_handlers.md`

[Открыть исходный файл](ru/code-documentation/stage_one_handlers.md)

#### Handlers Stage One

Stage One отвечает за filesystem inventory, фильтрацию, сортировку и content analysis DNS/Host датасетов. Он работает с raw/sorted файлами и JSON-картами, но не пишет PostgreSQL catalog и не создает normalized Parquet.

##### Общий поток

```mermaid
flowchart LR
  A["Raw datasets PATH_FOLDER_DATASETS"] --> B["analyze_dataset"]
  B --> C["path/file JSON в PATH_TEMP_DATA"]
  C --> D["filter_dataset только Host"]
  C --> E["sort DNS"]
  D --> F["sort Host"]
  E --> G["save_sort DNS"]
  F --> H["save_sort Host"]
  G --> I["dns_analyze"]
  H --> J["host_analyze"]
  I --> K["docs + reports + summary JSON"]
  J --> K
```

##### `json_handler` / `JsonDataManager`

Файл: `scripts/handlers/json_handler/json_data.py`.

`JsonDataManager` предоставляет минимальный контракт:

| Метод | Поведение |
|---|---|
| `ensure_directory()` | создает parent directory |
| `exists()` | проверяет наличие JSON file |
| `create(initial_data, overwrite=False)` | создает JSON, не перезаписывает без `overwrite=True` |
| `read(default=None)` | читает JSON object; если файла нет, возвращает default или `{}` |
| `write(data)` | полностью перезаписывает JSON; принимает только `dict` |
| `update(new_data)` | top-level merge и запись |

Пограничные случаи:

- JSON должен быть object/dict. List/scalar вызывает `ValueError`.
- Запись не атомарная: при аварийном завершении возможен частично записанный файл.
- Нет file locking; параллельные writes не защищены.

##### `analyze_dataset`

Файлы:

- `scripts/handlers/analyze_dataset/dns_dataset_handler.py`
- `scripts/handlers/analyze_dataset/host_dataset_handler.py`
- `scripts/handlers/analyze_dataset/router_analyze.py`

Команды:

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers analyze-dataset host-dataset-handler
```

Назначение: просканировать директории `PATH_DNS_DATASETS` или `PATH_HOST_DATASETS`, распределить файлы по ролям и сохранить path/name JSON.

Важно: handler проверяет наличие файла через filesystem walk, но не читает содержимое файлов.

###### Выходной контракт DNS

Файлы:

- `PATH_TEMP_DATA/dns-path-file.json`
- `PATH_TEMP_DATA/dns-file.json`

Контракт:

```json
{
  "TRAIN": ["/abs/path/file1.csv"],
  "TEST": ["/abs/path/file2.csv"],
  "VALIDATION": ["/abs/path/file3.pcap"],
  "EXPERIMENTS": []
}
```

Роли определяются по токенам пути:

| Role | Keywords |
|---|---|
| `TRAIN` | `train`, `training` |
| `TEST` | `test`, `testing` |
| `VALIDATION` | `validation`, `valid`, `val`, `dev`, `eval` |
| `EXPERIMENTS` | fallback для DNS, если role tokens не найдены |

###### Выходной контракт Host

Файлы:

- `PATH_TEMP_DATA/host-path-file.json`
- `PATH_TEMP_DATA/host-file.json`

Контракт:

```json
{
  "TRAIN": ["/abs/path/file1.log"],
  "TEST": ["/abs/path/file2.json"],
  "VALIDATION": ["/abs/path/file3.csv"]
}
```

Host fallback role в коде: `TEST`. Это риск: если путь не содержит role token, файл попадает в `TEST`. Для новых датасетов лучше не полагаться на fallback и обеспечить явные role directories.

Ошибки:

- пустой `PATH_*_DATASETS` -> `ValueError`;
- несуществующая директория -> `FileNotFoundError`;
- path не directory -> `NotADirectoryError`.

##### `filter_dataset`

Файл: `scripts/handlers/filter_dataset/filter_host_dataset_handler.py`.

Команда:

```bash
python manage.py handlers filter-dataset filter-host-dataset-handler
```

Фильтрация реализована только для Host datasets. DNS filter отсутствует.

Вход:

- `PATH_TEMP_DATA/host-path-file.json`
- `PATH_TEMP_DATA/host-file.json`

Выход:

- `PATH_TEMP_DATA/filter_dataset-host-path-file.json`
- `PATH_TEMP_DATA/filter_dataset-host-file.json`
- `PATH_FILTER_LOG`

Фильтр обязателен перед Host sort, потому что `HostDatasetSortHandler` читает именно `filter_dataset-host-*.json`.

В коде зашиты whitelist rules:

| Role | Разрешенные datasets |
|---|---|
| `TRAIN` | `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset` |
| `VALIDATION` | `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets` |
| `TEST` | `Unified-Host-Network-Dataset -LANL`, `ISOT-Cloud-IDS-Dataset`, `Dynamic-Malware-Analysis-Dataset` |

Примеры разрешенных suffix:

- ADFA: `.txt`, `.ghc`, `.csv`, `.netflow_ids`, `.xml`
- LID-DS 2021: `.sc`, `.json`
- OTRF: `.json`, `.cap`, `.pcap`, `.pcapng`
- ISOT: `.csv`
- Dynamic Malware: `.txt`, `.json`, `.bson`, `.log`

Технические риски:

- Извлечение имени датасета завязано на сегмент пути `host` и позицию `host/<role>/<dataset>`.
- Новые dataset names будут исключены без изменения кода.
- Whitelist не конфигурируется через JSON/YAML.
- Фильтр не проверяет содержимое файлов.

##### `sort`

Файлы:

- `scripts/handlers/sort/sort_dns_dataset_handler.py`
- `scripts/handlers/sort/sort_host_dataset_handler.py`

Команды:

```bash
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
```

Назначение: создать sorted tree:

```text
PATH_DNS_DATASETS_FILTER/
  TRAIN/<format>/
  TEST/<format>/
  VALIDATION/<format>/

PATH_HOST_DATASETS_FILTER/
  TRAIN/<format>/
  TEST/<format>/
  VALIDATION/<format>/
```

Материализация файла:

1. сначала `os.link` hardlink;
2. при ошибке fallback на `shutil.copy2`.

Коллизии имен решаются hash suffix по исходному пути. Если destination уже тот же file, он считается skipped existing.

Summary JSON:

- `PATH_TEMP_DATA/sort-dns-format-summary.json`
- `PATH_TEMP_DATA/sort-host-format-summary.json`

Summary fields:

```json
{
  "sorted_root_path": "...",
  "created_links_count": 0,
  "copied_files_count": 0,
  "skipped_existing_count": 0,
  "missing_source_count": 0,
  "name_mismatch_count": 0,
  "files_by_role_and_format": {
    "TRAIN": {"csv": 8}
  }
}
```

Ограничение: сортировка не регистрирует файлы в PostgreSQL. Catalog ingestion делает Stage Two.

##### `save_sort`

Файлы:

- `scripts/handlers/save_sort/save_sort_dns_path_handler.py`
- `scripts/handlers/save_sort/save_sort_host_path_handler.py`

Команды:

```bash
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
```

Назначение: обойти sorted tree и сохранить пути по `role/format`.

Выход:

- `PATH_TEMP_DATA/sort-path-dns-file.json`
- `PATH_TEMP_DATA/sort-path-dns-file-summary.json`
- `PATH_TEMP_DATA/sort-path-host-file.json`
- `PATH_TEMP_DATA/sort-path-host-file-summary.json`

Контракт:

```json
{
  "TRAIN": {
    "csv": ["/abs/sorted/TRAIN/csv/file.csv"],
    "pcap.csv": ["/abs/sorted/TRAIN/pcap.csv/file.pcap.csv"]
  },
  "TEST": {},
  "VALIDATION": {}
}
```

Эти JSON нужны для `dns_analyze` и `host_analyze`: content analyzers читают role/format bucket из `sort-path-*-file.json`.

##### `dns_analyze`

Файлы:

- `scripts/handlers/dns_analyze/router_dns.py`
- `scripts/handlers/dns_analyze/run_action.py`
- `scripts/handlers/dns_analyze/analyze_dns_*_dataset_handler.py`

Actions:

| Action | Bucket |
|---|---|
| `analyze-train-csv-content` | DNS `TRAIN/csv` |
| `analyze-train-pcap-content` | DNS `TRAIN/pcap` |
| `analyze-train-pcap-csv-content` | DNS `TRAIN/pcap.csv` |
| `analyze-test-csv-content` | DNS `TEST/csv` |
| `analyze-test-pcap-content` | DNS `TEST/pcap` |
| `analyze-test-pcap-csv-content` | DNS `TEST/pcap.csv` |
| `analyze-validation-pcap-content` | DNS `VALIDATION/pcap` |
| `analyze-validation-txt-content` | DNS `VALIDATION/txt` |

Выход:

- analysis summary JSON в `PATH_TEMP_DATA`;
- RU/EN docs в `docs/{ru,en}/analysis-dataset/dns/<role>`;
- RU/EN reports в `PATH_REPORT/{ru,en}/stage-one/analysis-dataset/dns/<role>`.

##### `host_analyze`

Файлы:

- `scripts/handlers/host_analyze/router_host.py`
- `scripts/handlers/host_analyze/run_action.py`
- `scripts/handlers/host_analyze/analyze_host_*_dataset_handler.py`

Actions покрывают train/validation/test buckets: `csv`, `json`, `json-1`, `log`, rotated logs, `cap`, `pcap`, `pcapng`, `bson`, `netflow_day`, `wls_day`, `txt`, `sc`, `ghc`, `xml`, Metricbeat-like logs.

Выход аналогичен DNS, но находится в `host/<role>`.

##### Статусы анализа

Stage One docs используют статусы:

| Статус | Значение |
|---|---|
| `READY_FOR_FEATURE_EXTRACTION` | формат можно подключать к feature extraction после стандартной нормализации |
| `NEEDS_CUSTOM_PARSER` | нужен специализированный parser или schema-aware обработчик |
| `PARTIALLY_SUPPORTED` | часть структуры читается, но есть mixed schema/partial labels/нестабильность |
| `BROKEN_OR_EMPTY` | bucket пустой или непригоден для дальнейшего анализа |

Эти статусы не являются PostgreSQL enum для Stage Two. Они используются как input к parser strategy и ручной приоритизации.

---

### Источник: `docs/ru/code-documentation/stage_two_overview.md`

[Открыть исходный файл](ru/code-documentation/stage_two_overview.md)

#### Обзор Stage Two

Stage Two переводит sorted filesystem datasets в catalog-backed normalized artifacts. Цель: сохранить raw files неизменными, зарегистрировать metadata, выбрать parser, записать normalized events в Parquet и подготовить основу для feature/model-ready layers без leakage.

##### Основные директории кода

```text
scripts/stage_two/
  cli.py
  storage/bootstrap.py
  ingestion/
  parser_registry/
  parsers/
  labels/
  normalization/
  parquet/
  features/
  model_ready/
  duckdb/
  quality/
  traceability/
  splitting/
  reports/
  readiness_check.py
  e2e_dry_run.py

scripts/db/
  config.py
  session.py
  models/
  repositories/
  migrations/

schemas/
  normalized/normalized_event_v1.json
  features/feature_artifact_v1.json
  model_ready/model_ready_v1.json
```

##### Поток данных

```mermaid
flowchart TD
  A["PATH_FOLDER_DATASETS_FILTER"] --> B["catalog-ingest"]
  B --> C["PostgreSQL: datasets, ingestion_runs, dataset_files"]
  D["schemas + parser_registry_seed.json"] --> E["seed-parser-registry"]
  E --> F["schema_versions + parser_registry"]
  C --> G["mark-ready"]
  F --> H["ParserResolver"]
  G --> I["normalize-format / normalize-all / normalize-dns / normalize-host"]
  H --> I
  I --> J["parser_runs"]
  I --> K["Parquet normalized"]
  K --> L["normalized_artifacts"]
  K --> M["DuckDB views/checks"]
  N["feature/model-ready writers"] --> O["feature_artifacts, preprocessing_artifacts, model_ready_artifacts"]
  O --> P["LeakageChecker"]
  O --> Q["TraceabilityService"]
```

##### Инициализация storage

Файл: `scripts/stage_two/storage/bootstrap.py`.

Команда:

```bash
python manage.py stage-two bootstrap-storage
```

Создает обязательную структуру в `PATH_DATA_STORAGE`, не удаляя существующие файлы. Bootstrap идемпотентный: существующие directories попадают в `existing`, новые в `created`.

##### Ingestion catalog

Файлы:

- `scripts/stage_two/ingestion/catalog_ingestion_service.py`
- `scripts/stage_two/ingestion/scanner.py`
- `scripts/stage_two/ingestion/file_hash_service.py`

Команда:

```bash
python manage.py stage-two catalog-ingest
```

Вход: `PATH_FOLDER_DATASETS_FILTER`.

Записывает:

- `ingestion_runs`;
- `datasets`;
- `dataset_files`.

Scanner определяет:

| Metadata | Источник |
|---|---|
| `branch` | части path: `dns`, `host`, `network`, `hybrid`; fallback `hybrid` |
| `role` | части path: `TRAIN`, `VALIDATION`, `TEST`; файлы без active role игнорируются |
| `source_format` | sorted bucket после role или filename suffix/compound suffix |
| `dataset_name` | path segment между branch и role, fallback `<branch>_<role>_<source_format>` |
| `dataset_slug` | lowercase slug |

Catalog ingestion рассчитывает SHA-256 потоковым чтением и делает upsert файлов по `(dataset_id, file_path)`.

Назначение статусов:

- `REGISTERED` по умолчанию;
- `EMPTY_FILE` для файлов нулевого размера;
- `UNSUPPORTED_FORMAT`, если inferred format находится вне known formats.

##### Seed parser registry

Файлы:

- `scripts/stage_two/parser_registry/parser_registry_seed.json`
- `scripts/stage_two/parser_registry/seed.py`
- `scripts/stage_two/parser_registry/resolver.py`
- `scripts/stage_two/normalization/schema_contracts.py`

Команда:

```bash
python manage.py stage-two seed-parser-registry
```

Действия:

1. Загружает `schemas/normalized/normalized_event_v1.json`.
2. Делает upsert row в `schema_versions` для `normalized_event/v1`.
3. Разворачивает compact parser seed groups в rows `parser_registry`.
4. Валидирует `parser_module.parser_class`.
5. Если active parser class отсутствует или не является `BaseParser`, row сохраняется с `is_active=false` и диагностикой в `config_json`.

##### Разрешение parser

`ParserResolver` выбирает active parser по правилу:

```text
branch + source_format + (supported_role == role OR supported_role IS NULL)
ORDER BY priority ASC, id ASC
```

Если parser не найден, `resolve_or_mark_unsupported()` помечает `dataset_files.status='UNSUPPORTED_FORMAT'`.

##### Сервисы normalization

Файлы:

- `scripts/stage_two/normalization/dns_service.py`
- `scripts/stage_two/normalization/host_service.py`
- `scripts/stage_two/normalization/runner.py`
- `scripts/stage_two/normalization/options.py`

Команды:

```bash
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two normalize-all --branch host --limit 100
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

`normalize-format` и `normalize-all` являются более контролируемыми routes: они не смешивают роли и форматы. Legacy `normalize-dns/host` выбирают ready files по branch.

Поток normalization:

1. Выбрать `dataset_files.status='READY_FOR_PARSING'`.
2. Разрешить parser metadata и schema version.
3. Создать или возобновить `parser_runs`.
4. Создать parser с `LabelResolver`.
5. Собрать `ParserContext`.
6. Потоково читать parse batches.
7. Записать normalized Parquet parts через `ParquetArtifactWriter`.
8. Зарегистрировать `normalized_artifacts`.
9. Завершить `parser_runs`.
10. Обновить `dataset_files.status`.
11. Сохранить parser run reports.

Маппинг статусов parser/file:

| Результат parser | `parser_runs.status` | `dataset_files.status` |
|---|---|---|
| все строки распарсены | `SUCCESS` | `PARSED` |
| часть строк распарсена, часть завершилась ошибкой | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| ошибка чтения или нет распарсенных строк | `FAILED` | `FAILED` |
| пустой файл | `SKIPPED` | `EMPTY_FILE` |
| unsupported format | `SKIPPED` | `UNSUPPORTED_FORMAT` |
| намеренно пропущенный helper file | `SKIPPED` | `SKIPPED` |

##### Разрешение labels

Файл: `scripts/stage_two/labels/resolver.py`.

Resolver возвращает canonical label fields для каждого normalized event. Отсутствующие labels преобразуются в:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Filename и embedded label hints отключены для `TEST` через `label_hints_allowed()`.

##### Запись Parquet

Файл: `scripts/stage_two/parquet/writer.py`.

Записывает:

- normalized events;
- feature rows;
- model-ready tables.

Compression по умолчанию: `zstd`.

PostgreSQL хранит только artifact metadata и paths. Большие данные остаются в Parquet.

##### Сервисы feature и model-ready

Файлы:

- `scripts/stage_two/features/contracts.py`
- `scripts/stage_two/features/writer.py`
- `scripts/stage_two/model_ready/contracts.py`
- `scripts/stage_two/model_ready/registry.py`

Текущее состояние:

- feature writer может писать prepared rows и регистрировать `feature_artifacts`;
- model-ready registry может писать/регистрировать X/y/sequence/split/preprocessing artifacts;
- orchestration feature extraction пока не оформлена как полный CLI pipeline;
- contracts enforce X excluded/forbidden columns и TRAIN-only preprocessing fit.

##### DuckDB и проверки

Файлы:

- `scripts/stage_two/duckdb/service.py`
- `scripts/stage_two/duckdb/sql/create_views.sql`
- `scripts/stage_two/quality/checkers.py`

Команды:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

DuckDB views:

- `normalized_all`;
- `features_all`;
- `model_ready_all`.

Проверки покрывают row counts, required columns, split contamination, schema mismatch, nulls, duplicates, role/branch domains, forbidden X columns, отсутствие TEST в TRAIN artifacts и preprocessing fit role.

##### Traceability

Файл: `scripts/stage_two/traceability/service.py`.

Команда:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Traceability разрешает цепочку:

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

Если любая связь отсутствует, `TraceabilityError` объясняет недостающий link.

##### Readiness и dry run

В репозитории есть `scripts/stage_two/readiness_check.py` и `scripts/stage_two/e2e_dry_run.py`. Они относятся к слоям operational validation. Основные production contracts при этом задаются CLI, ORM, schemas, parser registry и tests в `tests/stage_two`.

##### Ограничения текущей реализации

- Orchestration feature extraction не полностью оформлена как end-to-end CLI stage.
- Model-ready creation есть как registry/writer service, но нет полноценной команды сборки X/y для всех branches.
- `normalize-dns/host` legacy routes менее управляемы, чем `normalize-format`.
- Некоторые Stage One docs могут иметь статус `NEEDS_CUSTOM_PARSER`, даже если Stage Two уже содержит parser class для части формата; решающим является active parser registry + parser coverage.
##### Performance execution architecture

Stage Two normalization теперь имеет performance-oriented execution layer без изменения normalized event contract.

Основные файлы:

- `scripts/stage_two/execution/work_unit.py`;
- `scripts/stage_two/execution/planner.py`;
- `scripts/stage_two/execution/executor.py`;
- `scripts/stage_two/execution/runtime_settings.py`;
- `scripts/stage_two/execution/retry_policy.py`;
- `scripts/stage_two/execution/progress.py`;
- `scripts/stage_two/execution/format_policy.py`;
- `scripts/stage_two/benchmark.py`;
- `scripts/stage_two/quality/post_run_validation.py`.

Ключевое поведение:

- `WorkUnitPlanner` строит работу только для `dataset_files.status=READY_FOR_PARSING` и одного точного `branch/role/source_format`.
- `WorkUnitExecutor` использует `ProcessPoolExecutor` для CPU parsing и bounded future submission.
- Workers не делят одну SQLAlchemy session; каждый process открывает собственный DB/session context только там, где нужно.
- Resume пропускает successful normalized artifacts с подходящими parser/schema versions.
- Parser failures изолируются на уровне file/chunk и могут давать `PARTIAL_SUCCESS` для команды.
- Parsers используют `parse_batches` для streaming/batch parsing там, где возможно.
- Большие line-based files можно делить на registered chunks с parent trace metadata.
- Binary formats (`cap`, `pcap`, `pcapng`, `bson`) не делятся обычным line splitter.
- `ParquetArtifactWriter` пишет через atomic temp-file и валидирует output до artifact registration.
- `benchmark-normalization` измеряет throughput и оценивает достижимость `17 GB <= 3 hours`.
- `normalize-format` создает post-run validation report по counts, reconciliation, split separation, leakage и traceability.

Resource profiles:

| Profile | workers | batch_size | max_output_part_rows |
| --- | ---: | ---: | ---: |
| `safe` | 4 | 50000 | 100000 |
| `balanced` | 8 | 100000 | 250000 |
| `fast` | 12 | 200000 | 500000 |
| `aggressive` | 14 | 300000 | 750000 |

Format policy ограничивает рискованные форматы:

- PCAP/PCAPNG/CAP: low workers и `packet-summary` by default.
- BSON: low workers и moderate batches.
- JSON/JSONL: moderate workers.
- line-based logs/TXT/syscall traces: fast settings после benchmark validation.

Operational target:

- required throughput для 17 GB за 3 часа: около `5.67 GB/hour`;
- target на i7-14700KF / 64 GB RAM / M.2 SSD: `10-20+ GB/hour` для line-based formats;
- GPU остается extension point для feature/model-ready/training, а не default raw parser engine.

Safety invariants не меняются: raw files immutable, splits separate, `TEST` не используется для training/fit/tuning, labels не являются X features, missing labels/timestamps сохраняют explicit null/missing semantics, traceability остается полной.

---

### Источник: `docs/ru/code-documentation/storage_architecture.md`

[Открыть исходный файл](ru/code-documentation/storage_architecture.md)

#### Архитектура storage

##### Корень storage

`PATH_DATA_STORAGE` задается в `.env` и читается в `config.py`. Все generated artifacts, reports, temporary files, база DuckDB, backups и runtime config Stage Two должны находиться внутри этого корня.

Команда bootstrap:

```bash
python manage.py stage-two bootstrap-storage
```

##### Обязательная структура

`StorageBootstrapper.required_relative_paths()` создает:

```text
PATH_DATA_STORAGE/
  postgres/
  pgadmin/
  parquet/
    normalized/
      dns/TRAIN/
      dns/VALIDATION/
      dns/TEST/
      host/TRAIN/
      host/VALIDATION/
      host/TEST/
      network/TRAIN/
      network/VALIDATION/
      network/TEST/
      hybrid/TRAIN/
      hybrid/VALIDATION/
      hybrid/TEST/
    features/
      dns_features/
      host_syscall_features/
      host_eventlog_features/
      host_metrics_features/
      network_flow_features/
      hybrid_features/
      sequence_features/
    model_ready/
      tabular/
      labels/
      sequences/
      preprocessing/
      split_index/
  duckdb/
    sql/
    exports/
  logs/stage-two/
  backups/
    postgres_catalog/
    metadata_exports/
  temp_data/
    ingestion/
    parser_runs/
    normalization/
    duckdb/
  schemas/
    normalized/
    features/
    model_ready/
  reports/
    ru/stage-two/
      parser/
      normalization/
      quality/
      leakage/
      schema_mismatch/
    en/stage-two/
      parser/
      normalization/
      quality/
      leakage/
      schema_mismatch/
  config/
```

Фактический bootstrap также создает report group directories в `reports/ru/<group>` и `reports/en/<group>` для совместимости с текущими constants.

##### Пути storage для Stage One

Stage One использует:

| Config | Назначение |
|---|---|
| `PATH_FOLDER_DATASETS` | корень raw datasets |
| `PATH_DNS_DATASETS` | `PATH_FOLDER_DATASETS/dns` |
| `PATH_HOST_DATASETS` | `PATH_FOLDER_DATASETS/host` |
| `PATH_FOLDER_DATASETS_FILTER` | корень sorted/filtered datasets для Stage Two ingestion |
| `PATH_DNS_DATASETS_FILTER` | `PATH_FOLDER_DATASETS_FILTER/dns` |
| `PATH_HOST_DATASETS_FILTER` | `PATH_FOLDER_DATASETS_FILTER/host` |
| `PATH_TEMP_DATA` | JSON inventories и Stage One summaries |
| `PATH_REPORT` | корень reports Stage One и Stage Two |

Raw files в `PATH_FOLDER_DATASETS` не изменяются. `sort` создает hardlinks/copies в `PATH_FOLDER_DATASETS_FILTER`.

##### Пути Parquet

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

`ParquetArtifactWriter` возвращает абсолютный и относительный path. Относительный path сохраняется в PostgreSQL artifact tables.

##### Пути DuckDB

| Путь | Назначение |
|---|---|
| `duckdb/proposal_analytics.duckdb` | DuckDB database по умолчанию |
| `duckdb/sql/create_views.sql` | SQL template для views |
| `duckdb/exports/` | exports |

`DuckDBAnalyticsService` может создавать views напрямую из Parquet glob patterns. Он не копирует Parquet data в PostgreSQL.

##### Отчеты

| Тип отчета | Путь |
|---|---|
| DuckDB analytics | `reports/en/stage-two/quality/duckdb_analytics_report.json` |
| Quality report | `reports/{en,ru}/stage-two/quality/quality_report.json` |
| Leakage report | `reports/{en,ru}/stage-two/leakage/leakage_report.json` |
| Parser reports | генерируются `scripts/stage_two/reports` внутри storage reports |

##### Config и schemas

Исходные schemas проекта находятся в repository `schemas/`. Bootstrap также создает directories `PATH_DATA_STORAGE/schemas/...` для runtime copies/exports, если они нужны.

Текущий загрузчик схем читает:

- `schemas/normalized/normalized_event_v1.json`;
- `schemas/features/feature_artifact_v1.json`;
- `schemas/model_ready/model_ready_v1.json`.

##### Эксплуатационные ограничения

- `PATH_DATA_STORAGE` должен быть непустым для bootstrap, Parquet writer и DuckDB service.
- Generated artifacts должны использовать relative paths в catalog для portability.
- Raw datasets должны оставаться вне generated Parquet/report directories.
- Backups должны включать PostgreSQL catalog metadata и schema/config snapshots, а не копии raw data, если это явно не запланировано.

---

### Источник: `docs/ru/code-documentation/sqlalchemy_layer.md`

[Открыть исходный файл](ru/code-documentation/sqlalchemy_layer.md)

#### Слой SQLAlchemy

##### Расположение

```text
scripts/db/
  config.py
  session.py
  smoke_check.py
  models/
  repositories/
  migrations/
```

##### Конфигурация

Файл: `scripts/db/config.py`.

`load_database_settings()` читает:

| Env | Значение по умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | обязательное | строка подключения SQLAlchemy |
| `SQLALCHEMY_ECHO_SQL` | `false` | логирование SQL |
| `SQLALCHEMY_POOL_PRE_PING` | `true` | pre-ping подключений |

Если `DATABASE_URL` не задан, функция поднимает `ValueError`.

##### Управление сессиями

Файл: `scripts/db/session.py`.

`session_scope()`:

```python
@contextmanager
def session_scope(...):
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Свойства:

- commit транзакции после успешного блока;
- rollback при exception;
- close выполняется всегда;
- `expire_on_commit=False`;
- `autoflush=False`, `autocommit=False`.

Вложенные операции по отдельным файлам в normalization используют `session.begin_nested()`, чтобы failing file не обязательно ломал весь batch.

##### Модели

Модели находятся в `scripts/db/models` и экспортируются через `scripts/db/models/__init__.py`.

Ключевые модели:

- `Dataset`;
- `DatasetFile`;
- `IngestionRun`;
- `ParserRegistry`;
- `SchemaVersion`;
- `ParserRun`;
- `NormalizedArtifact`;
- `FeatureArtifact`;
- `PreprocessingArtifact`;
- `ModelReadyArtifact`;
- `LabelMappingRule`;
- `DataQualityReport`.

Общие constants: `scripts/db/models/constants.py`.

Важные constants:

```text
BRANCH_VALUES = dns, host, network, hybrid
ROLE_VALUES = TRAIN, VALIDATION, TEST, EXPERIMENTS
ACTIVE_DATASET_ROLE_VALUES = TRAIN, VALIDATION, TEST
ACTIVE_CATALOG_SOURCE_GROUP = PATH_FOLDER_DATASETS_FILTER
```

##### Репозитории

Repositories инкапсулируют записи/запросы и не управляют commit самостоятельно.

| Repository | Назначение |
|---|---|
| `DatasetRepository` | получение/создание datasets |
| `IngestionRepository` | start/finish/failed для ingestion runs |
| `DatasetFileRepository` | bulk upsert файлов, выбор ready files, обновление статуса |
| `ParserRepository` | parser registry rows и жизненный цикл parser run |
| `SchemaRepository` | регистрация schema version |
| `ArtifactRepository` | регистрация normalized/feature/model-ready artifacts |
| `PreprocessingRepository` | регистрация preprocessing artifacts |
| `LabelRepository` | поиск label mapping |
| `DataQualityRepository` | регистрация quality/leakage reports |

`DatasetFileRepository.bulk_upsert_files()` использует PostgreSQL `ON CONFLICT` по `(dataset_id, file_path)`. Если hash файла изменился, статус становится `CHANGED`; иначе существующий статус сохраняется.

##### Миграции Alembic

Конфигурация: `scripts/db/migrations/alembic.ini`.

Миграция:

```text
scripts/db/migrations/versions/5a38996dff5f_create_stage_two_catalog_schema.py
```

Применение:

```bash
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m alembic -c scripts/db/migrations/alembic.ini current
```

Миграция создает все таблицы catalog Stage Two:

- `data_quality_reports`;
- `datasets`;
- `ingestion_runs`;
- `label_mapping_rules`;
- `parser_registry`;
- `schema_versions`;
- `dataset_files`;
- `parser_runs`;
- `normalized_artifacts`;
- `feature_artifacts`;
- `preprocessing_artifacts`;
- `model_ready_artifacts`.

##### Smoke-проверка

Файл: `scripts/db/smoke_check.py`.

`run_smoke_checks()`:

- создает dataset;
- проверяет unique/check constraints;
- создает ingestion run;
- вставляет dataset file;
- создает parser registry/schema/parser run;
- регистрирует normalized, feature, preprocessing и model-ready artifacts;
- проверяет, что `PreprocessingArtifact(fitted_on_role='TEST')` падает;
- создает quality report;
- откатывает все smoke data в конце.

Рекомендуемая команда:

```bash
python - <<'PY'
from scripts.db.smoke_check import run_smoke_checks
print(run_smoke_checks())
PY
```

Требует рабочий `DATABASE_URL` и примененные migrations.

##### Эксплуатационные замечания

- Методы repository ожидают session, управляемую снаружи.
- Ни один repository не должен хранить большие row tables в PostgreSQL.
- DB constraints защищают домены branch/role/status, но сами по себе не предотвращают ML leakage; нужны model-ready contracts и leakage checks.
- Для долгих запусков normalization предпочитайте `normalize-format` с ограниченным `--batch-size` и явным `--limit`.

---

### Источник: `docs/ru/code-documentation/postgresql_catalog.md`

[Открыть исходный файл](ru/code-documentation/postgresql_catalog.md)

#### PostgreSQL Catalog

PostgreSQL catalog хранит metadata, статусы, связи, пути, хеши и отчеты. Большие normalized/features/model-ready таблицы в PostgreSQL не пишутся: они хранятся в Parquet.

##### Зачем нужен catalog

- регистрировать identity датасетов и файлов;
- хранить file hashes и обнаруживать изменения;
- фиксировать статусы ingestion/parser run;
- хранить parser registry и schema versions;
- связывать normalized, feature и model-ready artifacts;
- регистрировать quality/leakage reports;
- обеспечивать traceability.

##### Таблицы

###### `datasets`

Назначение: dataset-level metadata для raw sources и split roles.

Основные поля: `id`, `name`, `slug`, `branch`, `role`, `source_group`, `description`, `dataset_version`, `source_url`, `license_name`, `is_active`, `metadata_json`.

Связи:

- `datasets.id -> dataset_files.dataset_id`;
- `datasets.id -> normalized_artifacts.dataset_id`;
- `datasets.id -> feature_artifacts.dataset_id`.

Пишут: `CatalogIngestionService` через `DatasetRepository.get_or_create_dataset`.

Читают: normalization services, traceability, repositories.

Статусы: `is_active`; `branch` в `dns, host, network, hybrid`; `role` в `TRAIN, VALIDATION, TEST, EXPERIMENTS`.

###### `ingestion_runs`

Назначение: один запуск directory scanning/catalog ingestion.

Поля: `run_uid`, `root_path`, `root_path_kind`, `branch`, `role`, `started_at`, `finished_at`, `status`, counters `files_seen/new/existing/changed/failed`, `error_message`, `report_path`.

Статусы: `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`.

Пишут: `IngestionRepository`.

Читают: audit/reporting, dataset file trace.

###### `dataset_files`

Назначение: catalog record для raw/sorted file.

Поля: `dataset_id`, `ingestion_run_id`, `file_path`, `relative_path`, `file_name`, `file_extension`, `source_format`, `file_size_bytes`, `file_hash_sha256`, `file_modified_at`, `role`, `branch`, `status`, parser/label/timestamp/encoding hints, `metadata_json`, `error_message`.

Статусы:

```text
DISCOVERED, REGISTERED, CHANGED, EMPTY_FILE, UNSUPPORTED_FORMAT,
READY_FOR_PARSING, PARSED, PARTIALLY_PARSED, FAILED, SKIPPED
```

Пишут:

- `CatalogIngestionService`;
- `MarkReadyService`;
- `ParserResolver.resolve_or_mark_unsupported`;
- normalization services.

Читают:

- `NormalizeFormatRunner`;
- `NormalizeAllRunner`;
- normalization services;
- traceability.

###### `parser_registry`

Назначение: metadata стратегии parser.

Поля: `parser_name`, `parser_version`, `branch`, `source_format`, `supported_role`, `normalized_schema_name`, `normalized_schema_version`, `parser_module`, `parser_class`, `priority`, `is_active`, `supports_streaming`, `requires_external_tools`, `external_tools_json`, `config_json`.

Пишут: `ParserRegistrySeeder`.

Читают: `ParserResolver`, parser coverage, normalization.

Ограничение: parser class должен существовать и наследовать `BaseParser`; иначе seed отключает active row.

###### `schema_versions`

Назначение: metadata версионированных schema contracts.

Поля: `schema_name`, `schema_version`, `layer`, `branch`, `schema_path`, `schema_hash_sha256`, `is_active`, `description`, `columns_json`.

Пишут: `NormalizedSchemaRegistry.register_contract`, `SchemaRepository`.

Читают: `ParserResolver.resolve_schema_version`, smoke checks, artifact registration.

Layers: `normalized`, `features`, `model_ready`.

###### `parser_runs`

Назначение: одна попытка parsing/normalization для raw file.

Поля: `run_uid`, `file_id`, `parser_registry_id`, `parser_name`, `parser_version`, `schema_version_id`, `started_at`, `finished_at`, `status`, `rows_read`, `rows_parsed`, `rows_failed`, `events_emitted`, `output_parquet_path`, `error_message`, `warning_count`, `metadata_json`, `report_path`.

Статусы: `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`.

Пишут: DNS/Host normalization services через `ParserRepository`.

Читают: `TraceabilityService`, artifact repositories, reports.

###### `normalized_artifacts`

Назначение: registry row для normalized Parquet output.

Поля: `artifact_uid`, `dataset_id`, `file_id`, `parser_run_id`, `schema_version_id`, `role`, `branch`, `modality`, `source_format`, `normalized_path`, `schema_name`, `schema_version`, `row_count`, `event_count`, `file_size_bytes`, `content_hash_sha256`, status, timestamp и label distributions, `metadata_json`.

Статусы: `PENDING`, `RUNNING`, `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED`.

Пишут: `ParquetArtifactWriter.register_normalized_artifact`.

Читают: feature writer, traceability, DuckDB via Parquet path.

###### `feature_artifacts`

Назначение: registry row для feature Parquet output.

Поля: `artifact_uid`, `dataset_id`, `normalized_artifact_id`, `role`, `branch`, `feature_group`, `feature_path`, schema name/version, row/sample/feature/entity/window counts, label distribution, excluded columns, status, metadata.

Пишут: `FeatureArtifactWriter`.

Читают: model-ready registry, preprocessing registry, traceability.

###### `preprocessing_artifacts`

Назначение: metadata для scaler/encoder/imputer/preprocessing object.

Поля: `artifact_uid`, `branch`, `feature_group`, `preprocessing_type`, `artifact_path`, `fitted_on_role`, `fitted_on_feature_artifact_id`, schema/object versions, columns/params JSON, status.

DB constraint: `fitted_on_role = 'TRAIN'`.

Пишут: `ModelReadyRegistryService.register_preprocessing_artifact`.

Читают: `LeakageChecker._preprocessing_fit_role_check`, model-ready artifacts.

###### `model_ready_artifacts`

Назначение: final metadata для model-ready X/y/sequence/split/preprocessing.

Поля: `artifact_uid`, `feature_artifact_id`, `preprocessing_artifact_id`, `role`, `branch`, `data_type`, `artifact_path`, schema name/version, sample/feature counts, label distribution, excluded columns, sequence length, status, metadata.

Data types: `X`, `y`, `sequence`, `split_index`, `preprocessing_metadata`.

Пишут: `ModelReadyRegistryService`.

Читают: `LeakageChecker`, `TraceabilityService`, DuckDB views.

###### `label_mapping_rules`

Назначение: explainable rules для назначения labels.

Поля: `rule_uid`, `rule_name`, `branch`, `role`, `source_format`, `dataset_name_pattern`, `file_name_pattern`, `source_field`, `source_value_pattern`, canonical label fields, `priority`, `is_active`, `description`.

Пишут: manual seed/config или repository.

Читают: `LabelResolver` через `LabelRepository.find_matching_rules`.

###### `data_quality_reports`

Назначение: registry для quality/leakage/schema reports.

Поля: `report_uid`, `artifact_type`, `artifact_id`, `check_group`, `check_name`, `status`, `severity`, row counters, missing/duplicate/schema/leakage counts, label/timestamp distributions, `details_json`, `report_path`.

Значения статуса: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `BLOCKED`.

Severity values: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

Пишут:

- `DuckDBAnalyticsService.register_report`;
- `register_quality_report`.

Читают: audit/reporting/CI gating.

##### Traceability chain

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

`TraceabilityService` требует наличие каждого link. `feature_artifacts.normalized_artifact_id` и `model_ready_artifacts.feature_artifact_id` nullable в schema, поэтому production model-ready artifact должен заполнять эти поля, иначе traceability будет неполной.

##### Почему не хранить большие таблицы в PostgreSQL

- normalized/events/features/model-ready rows могут быть на сотни тысяч или миллионы строк;
- PostgreSQL catalog нужен для metadata и lineage, а не для аналитического сканирования больших columnar datasets;
- Parquet + DuckDB дают columnar storage и SQL-проверки без перегрузки catalog DB;
- backups catalog metadata остаются компактными.

---

### Источник: `docs/ru/code-documentation/parser_strategy.md`

[Открыть исходный файл](ru/code-documentation/parser_strategy.md)

#### Стратегия парсеров

Стратегия парсеров состоит из seed JSON, PostgreSQL `parser_registry`, `ParserResolver`, конкретных parser classes и контрактов статусов парсинга.

##### Заполнение registry

Seed-файл: `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Команда seed:

```bash
python manage.py stage-two seed-parser-registry
```

Каждая parser group задает:

| Поле | Значение |
|---|---|
| `parser_name` | логический parser id |
| `parser_version` | версия parser |
| `branch` | `dns` или `host` в текущем seed |
| `source_formats` | один или несколько source format buckets |
| `supported_roles` | null для всех ролей или явный список ролей |
| `normalized_schema_name/version` | целевая normalized schema |
| `parser_module` | Python module |
| `parser_class` | имя class |
| `priority` | меньшее значение имеет приоритет |
| `supports_streaming` | registry metadata |
| `requires_external_tools` | registry metadata |

Валидация seed импортирует класс и проверяет `issubclass(BaseParser)`. Отсутствующие классы сохраняются как inactive rows с диагностикой.

##### Разрешение parser

Файл: `scripts/stage_two/parser_registry/resolver.py`.

Запрос выбора:

```text
branch == dataset_file.branch
source_format == dataset_file.source_format
is_active == true
supported_role == dataset_file.role OR supported_role IS NULL
ORDER BY priority, id
```

Если подходящая запись не найдена, file получает статус `UNSUPPORTED_FORMAT`.

##### Базовый контракт parser

Файл: `scripts/stage_two/parsers/base.py`.

Конкретный parser должен реализовать:

```python
class MyParser(BaseParser):
    parser_name = "..."
    parser_version = "v1"

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        ...
```

Потоковые parsers должны переопределять `parse_batches()`.

`ParserContext` передает catalog metadata:

```text
dataset_id, file_id, dataset_name, dataset_role, branch, source_format,
source_file_path, source_file_hash, parser_run_id, metadata
```

`ParserResult` передает counters, events, warnings, bytes read, error samples и optional status override.

##### Маппинг статусов

| Условие parser | Статус parser | `parser_runs.status` | `dataset_files.status` |
|---|---|---|---|
| строки распарсены, ошибок нет | `SUCCESS` | `SUCCESS` | `PARSED` |
| часть строк распарсена, часть завершилась ошибкой | `PARTIAL_SUCCESS` | `PARTIAL_SUCCESS` | `PARTIALLY_PARSED` |
| ни одна строка не распарсена | `FAILED` | `FAILED` | `FAILED` |
| ошибка чтения | `FAILED` | `FAILED` | `FAILED` |
| empty file | `EMPTY_FILE` | `SKIPPED` | `EMPTY_FILE` |
| unsupported format | `UNSUPPORTED_FORMAT` | `SKIPPED` | `UNSUPPORTED_FORMAT` |
| intentionally skipped | `SKIPPED` | `SKIPPED` | `SKIPPED` |

В формулировке задачи упомянут `PARTIALLY_PARSED`; в текущем коде это статус файла, а статус parser run равен `PARTIAL_SUCCESS`.

##### Классы DNS parser

| Класс | Модуль | Source formats | Примечания |
|---|---|---|---|
| `DnsCsvParser` | `scripts.stage_two.parsers.dns` | `csv` | DNS CSV с учетом схемы, поддерживает TEST CSV без header |
| `DnsPcapCsvParser` | `scripts.stage_two.parsers.dns` | `pcap.csv` | расширяет обработку DNS CSV для CSV, полученных из packet data |
| `DnsTxtDomainListParser` | `scripts.stage_two.parsers.dns` | `txt` для `VALIDATION` | parser списков доменов |
| `DnsPacketCaptureParser` | `scripts.stage_two.parsers.packet` | `cap`, `pcap`, `pcapng` | packet summary parser, DNS modality для DNS packets |

##### Классы Host parser

| Класс | Модуль | Source formats | Примечания |
|---|---|---|---|
| `HostCsvParser` | `scripts.stage_two.parsers.host` | `csv` | host CSV/event/metadata tables |
| `HostJsonLinesParser` | `scripts.stage_two.parsers.host` | `json`, `json-1` | JSON lines, arrays, objects и смешанная telemetry |
| `HostLineLogParser` | `scripts.stage_two.parsers.host` | многие `*.log`, rotated logs, `messages`, `syslog`, `mainlog` | line-oriented log parser |
| `HostSyscallTraceParser` | `scripts.stage_two.parsers.host` | `txt`, `sc`, `ghc` | syscall/API traces |
| `HostPacketCaptureParser` | `scripts.stage_two.parsers.packet` | `cap`, `pcap`, `pcapng` для `TRAIN`, `VALIDATION` | host network packet summaries |
| `HostBsonSandboxParser` | `scripts.stage_two.parsers.bson` | `bson` для `TEST` | BSON sandbox process/API telemetry |

Дополнительные реализованные и seed-нутые классы:

| Класс | Модуль | Source formats |
|---|---|---|
| `HostXmlParser` | `scripts.stage_two.parsers.host` через import from `xml.py` | `xml` |
| `HostNetflowParser` | `scripts.stage_two.parsers.host` через import from `netflow.py` | `netflow_day`, `netflow_ids`, `wls_day` |

Дополнительно реализовано, но не включено напрямую в текущий seed:

| Класс | Модуль | Примечания |
|---|---|---|
| `HostMetricbeatParser` | `scripts.stage_two.parsers.metrics` | используется/импортируется для поддержки Metricbeat-like telemetry |

##### Неподдерживаемые форматы

Неподдерживаемый формат означает, что для `(branch, role, source_format)` нет active row в parser registry. Обработка:

1. `ParserResolver.resolve_or_mark_unsupported()` выставляет `dataset_files.status='UNSUPPORTED_FORMAT'`.
2. `normalize-format` возвращает status `UNSUPPORTED_FORMAT`, если для выбранных файлов нет parser.
3. Parser coverage report показывает gaps.

##### Обработка ошибок

- Ошибки парсинга отдельных строк увеличивают `rows_failed` и сохраняют ограниченные error samples.
- Исключения parser помечают `parser_runs.status='FAILED'` и `dataset_files.status='FAILED'`.
- `save_parser_run_reports()` пишет parser diagnostics.
- `STAGE_TWO_MAX_ERROR_SAMPLES` ограничивает error samples.

##### Чеклист расширения parser

1. Добавить parser class в `scripts/stage_two/parsers`.
2. Наследовать `BaseParser`.
3. Отдавать events через `base_event()`.
4. Сохранять `timestamp_type`, `event_index`, labels и traceability fields.
5. Добавить entry в parser registry seed.
6. Запустить parser tests и `python manage.py stage-two seed-parser-registry`.
7. Запустить `python manage.py stage-two parser-coverage <branch>`.

---

### Источник: `docs/ru/code-documentation/normalized_event_schema.md`

[Открыть исходный файл](ru/code-documentation/normalized_event_schema.md)

#### Схема normalized event

Файл схемы: `schemas/normalized/normalized_event_v1.json`.

Код регистрации: `scripts/stage_two/normalization/schema_contracts.py`.

Таблица catalog: `schema_versions`.

##### Назначение

`normalized_event/v1` задает единый event-level контракт для DNS, host, network и hybrid источников. Parsers обязаны возвращать events с обязательными normalized fields. `BaseParser.validate_result()` проверяет наличие required fields, а schema JSON фиксирует полный field list и null policy.

##### Обязательные поля parser-level validation

`scripts/stage_two/parsers/base.py` требует наличие:

```text
event_uid
dataset_name
dataset_role
branch
source_format
source_file_path
parser_name
parser_version
schema_name
schema_version
timestamp_type
entity_type
event_type
modality
label_source
label_status
created_at
```

Schema JSON дополнительно описывает nullable/type/allowed values для всех canonical fields.

##### Поля traceability

| Field | Назначение |
|---|---|
| `event_uid` | stable event identity, обычно hash/context/index |
| `dataset_id` | FK-like catalog id, nullable для non-catalog contexts |
| `file_id` | raw dataset file id |
| `dataset_name` | dataset name из catalog/context |
| `dataset_role` | `TRAIN`, `VALIDATION`, `TEST`, `EXPERIMENTS` |
| `branch` | `dns`, `host`, `network`, `hybrid` |
| `source_format` | catalog source format |
| `source_file_path` | relative или absolute path raw/sorted source |
| `source_file_hash` | SHA-256 from catalog |
| `parser_name`, `parser_version` | parser identity |
| `parser_run_id` | parser run catalog id |
| `schema_name`, `schema_version` | normalized schema identity |

Эти поля нужны для downstream traceability и audits. Они не должны попадать в model-ready X features.

##### Контракт timestamp

Поля:

- `timestamp`: nullable UTC timestamp;
- `timestamp_source`: source column/header/packet header/etc.;
- `timestamp_type`: required enum;
- `event_index`: nullable индекс порядка события.

Допустимые `timestamp_type`:

| Value | Значение |
|---|---|
| `absolute` | source содержит absolute timestamp |
| `relative` | source содержит relative timestamp/delta |
| `event_order` | absolute time отсутствует, но порядок событий значим |
| `missing` | нет времени и нет надежного order timestamp |

Правила:

- `timestamp` может быть `null`.
- Отсутствующее время нельзя заменять текущим временем.
- `created_at` фиксирует время создания normalized row, но не является временем события.
- Если timestamp отсутствует, parser должен использовать `timestamp_type='missing'` или `event_order` и сохранять `event_index`.

##### Поля DNS

DNS-specific fields:

- `domain`;
- `query_domain`;
- `qtype`;
- `qclass`;
- `ttl`;
- `rcode`;
- network endpoints: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`.

DNS parsers также могут хранить source-specific values в `features_json`, `raw_fields_json`, `metadata_json`.

##### Поля Host

Host-specific fields:

- `host_name`;
- `user_name`;
- `process_id`;
- `process_name`;
- `parent_process_id`;
- `parent_process_name`;
- `syscall_name`;
- `event_id`;
- `command_line`;
- `file_path`;
- metrics: `metric_name`, `metric_value`.

Host parsers могут отдавать modalities вроде `host`, `host_metric`, `sandbox`, `host_network_packet`.

##### Поля network/hybrid

Network/hybrid data использует:

- endpoint fields `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`;
- DNS fields, если packet содержит DNS;
- `modality` для различения packet/flow/DNS/host events;
- `features_json` для derived flow/packet metrics.

##### Поля labels

Canonical labels:

| Поле | Смысл |
|---|---|
| `label_binary` | `0`, `1` или null |
| `label_family` | high-level label family, например benign/malware/dns_exfiltration |
| `label_subtype` | lower-level label subtype |
| `label_source` | `embedded_column`, `filename`, `scenario_metadata`, `external_label_file`, `ids_alert`, `ground_truth_csv`, `none` |
| `label_status` | `explicit_label`, `inferred_label`, `weak_label`, `partial_label`, `unlabeled`, `conflicting_label` |
| `label_confidence` | nullable confidence |
| `label_mapping_rule_id` | rule id или source marker |

Контракт unlabeled event:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Отсутствующий label не равен benign.

##### Поля JSON

| Field | Назначение |
|---|---|
| `features_json` | normalized low-level source features, полезные до feature extraction |
| `raw_fields_json` | source fields/raw row fragments для audit/debug |
| `metadata_json` | parser/source metadata, warnings, schema hints, helper flags |

`ParquetArtifactWriter` сериализует columns с окончанием `_json` в детерминированные JSON strings перед PyArrow inference.

##### Политика null

Schema JSON явно фиксирует:

- missing source field -> JSON null / SQL NULL / Parquet null;
- missing labels -> unlabeled fields, not benign;
- missing timestamps -> `timestamp=null`, `timestamp_type=missing`;
- ordered streams должны передавать `event_index`;
- статистики `TEST` нельзя использовать для fit/tuning/feature selection/model training.

---

### Источник: `docs/ru/code-documentation/label_resolver.md`

[Открыть исходный файл](ru/code-documentation/label_resolver.md)

#### Разрешение labels

Файл: `scripts/stage_two/labels/resolver.py`.

Цель: формировать canonical label fields для normalized events, не трактовать missing labels как benign и не разрешать filename heuristics для TEST.

##### Источники

Кандидаты labels могут поступать из:

| Источник | Значение в коде | Смысл |
|---|---|---|
| Embedded columns | `embedded_column` | прямые поля вроде `label`, `target`, `is_attack`, `attack_cat` |
| External rules/config | `external_label_file`, `ground_truth_csv`, etc. | DB/config mapping rules |
| Scenario metadata | `scenario_metadata` | contextual labels из scenario/rule metadata |
| Filename | `filename` | консервативные filename tokens только для non-TEST |
| IDS alert | `ids_alert` | слабый alert-like signal |
| None | `none` | явный unlabeled result |

Приоритет источников в коде:

```text
embedded_column < ground_truth_csv/external_label_file < scenario_metadata
< filename < ids_alert < none
```

##### Встроенные labels

Распознаваемые fields:

```text
label_binary, label, labels, target, class, is_attack, is_malicious,
malicious, attack, attack_cat, attack_category, attack_subcat,
is_executing_exploit, exploit
```

Для `TEST` embedded/filename/IDS hint candidates блокируются условием `label_hints_allowed(context) == False`. Это сделано намеренно, чтобы избежать TEST leakage и загрязнения evaluation через filename heuristic.

##### Правила mapping

Правила могут загружаться из:

- `PATH_DATA_STORAGE/config/label_mapping_rules.json` через `LABEL_MAPPING_RULES_CONFIG`;
- PostgreSQL `label_mapping_rules` через `LabelRepository`.

Rule matching может использовать:

- branch;
- role;
- source_format;
- dataset_name_pattern;
- file_name_pattern;
- source_field;
- source_value_pattern.

Выходные fields правила:

- `label_binary`;
- `label_family`;
- `label_subtype`;
- `label_source`;
- `label_status`;
- `label_confidence`;
- `label_mapping_rule_id`.

##### Labels из имени файла

Filename labels разрешены только при условии:

```python
context.dataset_role.upper() != "TEST"
```

Распознаваемые benign tokens:

```text
0, false, benign, normal, clean, legitimate
```

Распознаваемые malicious/family tokens:

```text
1, true, attack, malicious, exploit, malware, phishing, spam,
exfil, exfiltration, tunnel, tunneling, dga, nmap, hping,
masscan, zmap
```

TEST filename heuristic отключен. Его нельзя включать для evaluation datasets.

##### Отсутствующие labels

Отсутствующие labels дают:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_subtype": null,
  "label_source": "none",
  "label_status": "unlabeled",
  "label_confidence": null,
  "label_mapping_rule_id": null
}
```

Это жесткий инвариант: отсутствие label не означает benign.

##### Weak и inferred labels

| Статус | Использование |
|---|---|
| `explicit_label` | trusted direct label |
| `inferred_label` | inference по filename/scenario/rule |
| `weak_label` | weak signals, например IDS alert |
| `partial_label` | partial coverage или window/scenario labels |
| `unlabeled` | reliable label отсутствует |
| `conflicting_label` | конфликт candidates с одинаковым priority |

Weak/inferred labels должны сопровождаться `label_source`, `label_status`, `label_confidence` и желательно `label_mapping_rule_id`.

##### Конфликты

Если top-priority candidates расходятся по `label_binary` или `label_family`, resolver возвращает:

```json
{
  "label_binary": null,
  "label_family": null,
  "label_source": "<source>",
  "label_status": "conflicting_label",
  "label_confidence": 0.0
}
```

Downstream supervised training не должен неявно преобразовывать `conflicting_label` или `unlabeled` в benign.

##### Канонические label fields

Normalized schema и model-ready contracts трактуют эти поля как label/leakage fields:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
```

Они могут присутствовать в normalized или y/analysis artifacts, но не в model-ready X artifacts.

---

### Источник: `docs/ru/code-documentation/parquet_and_duckdb.md`

[Открыть исходный файл](ru/code-documentation/parquet_and_duckdb.md)

#### Parquet и DuckDB артефакты

##### Почему Parquet

Parquet используется для больших сгенерированных таблиц:

- normalized events;
- feature artifacts;
- model-ready artifacts.

PostgreSQL catalog хранит metadata и paths, а не табличные данные строк. Это сохраняет catalog компактным и позволяет DuckDB делать SQL-проверки поверх columnar data.

##### Запись Parquet

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

##### Пути артефактов

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

##### Регистрация в catalog

| Метод writer | Таблица catalog |
|---|---|
| `register_normalized_artifact()` | `normalized_artifacts` |
| `register_feature_artifact()` | `feature_artifacts` |
| `register_model_ready_artifact()` | `model_ready_artifacts` |

В catalog сохраняются relative paths:

- `normalized_artifacts.normalized_path`;
- `feature_artifacts.feature_path`;
- `model_ready_artifacts.artifact_path`.

##### Сервис DuckDB

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

##### Проверки DuckDB

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

##### SQL-шаблон

`scripts/stage_two/duckdb/sql/create_views.sql` содержит прямой SQL template с placeholder `${PATH_DATA_STORAGE}`. Python service безопаснее для runtime, потому что обрабатывает empty views и escaping путей.

---

### Источник: `docs/ru/code-documentation/data_quality_checks.md`

[Открыть исходный файл](ru/code-documentation/data_quality_checks.md)

#### Проверки качества данных

Код проверок:

- `scripts/stage_two/duckdb/service.py`;
- `scripts/stage_two/quality/checks.py`;
- `scripts/stage_two/quality/checkers.py`.

##### Аналитические проверки DuckDB

Команда:

```bash
python manage.py stage-two run-duckdb-checks
```

Проверки:

| Проверка | Область | Условие отказа |
|---|---|---|
| `row_counts_*` | normalized/features/model-ready views | не падает; формирует counts |
| `missing_required_columns_*` | каждое view | отсутствуют required columns |
| `split_contamination` | `model_ready_all` | TEST rows присутствуют в TRAIN model-ready artifacts |
| `schema_mismatch` | все views | mismatch required columns |

Отчет:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/duckdb_analytics_report.json
```

Регистрация в catalog:

- table: `data_quality_reports`;
- `check_group='duckdb'`;
- severity `ERROR`, если есть failed checks, иначе `INFO`.

##### DataQualityChecker

Класс: `DataQualityChecker`.

Проверки:

| Группа проверок | Детали |
|---|---|
| Обязательные columns | использует DuckDB `REQUIRED_COLUMNS` |
| Null counts | считает nulls в required columns, присутствующих во view |
| Duplicate keys | `event_uid` для normalized, `sample_uid` для features/model-ready |
| Role/branch domains | валидирует значения `role`, `dataset_role`, `branch` |

Выходные отчеты:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/quality_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/quality/quality_report.json
```

Опциональная регистрация в catalog выполняется через `DataQualityRepository`.

Severity:

- successful checks: `INFO`;
- failed data quality checks: `ERROR`.

##### LeakageChecker

Подробности leakage описаны в [data_leakage_prevention.md](ru/code-documentation/data_leakage_prevention.md). Checker пишет:

```text
PATH_DATA_STORAGE/reports/en/stage-two/leakage/leakage_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/leakage/leakage_report.json
```

Severity для failed leakage report: `CRITICAL`.

##### Контракт отчета

`QualityCheckResult`:

```text
check_name
status
severity
rows_total
rows_failed
details
```

`QualityReportResult`:

```text
check_group
status
severity
report_paths
checks
```

##### Критические нарушения

CRITICAL считаются:

- label/source/leakage columns с non-null values в model-ready X files;
- TEST rows в TRAIN model-ready artifacts;
- preprocessing artifact с fit на role, отличной от TRAIN.

Эти нарушения должны блокировать использование model-ready artifact для training.

---

### Источник: `docs/ru/code-documentation/data_leakage_prevention.md`

[Открыть исходный файл](ru/code-documentation/data_leakage_prevention.md)

#### Предотвращение data leakage

Предотвращение leakage обеспечивается документацией, контрактами, runtime validation и DuckDB checks. Полагаться только на соглашения небезопасно.

##### Жесткие правила

1. `TEST` никогда не используется для training, preprocessing fit, encoder/scaler fit, threshold tuning или feature selection.
2. `TRAIN`, `VALIDATION`, `TEST` остаются физически разделенными по role в Parquet paths.
3. Labels хранятся отдельно от X-признаков.
4. Model-ready X artifacts не должны содержать label/source/traceability leakage columns.
5. Отсутствующие labels получают статус `unlabeled`, а не benign.
6. Filename heuristic для TEST отключен.

##### Контроль в коде

| Правило | Код |
|---|---|
| X forbidden columns | `scripts/stage_two/model_ready/contracts.py::validate_x_columns` |
| Исключенные колонки feature layer | `scripts/stage_two/features/contracts.py::X_EXCLUDED_COLUMNS` |
| TRAIN-only preprocessing | `validate_preprocessing_fit_role()` и DB check constraint |
| Отключение TEST filename heuristic | `LabelResolver.label_hints_allowed()` |
| Отчет leakage | `LeakageChecker` |

##### Запрещенные X columns

Текущий код использует `X_EXCLUDED_COLUMNS`/`X_FORBIDDEN_COLUMNS`. Обязательный forbidden list из задачи покрыт и расширен реализацией:

```text
label_binary
label_family
label_subtype
label_source
label_status
label_confidence
label_mapping_rule_id
label
labels
target
class
is_attack
is_malicious
malicious
attack
attack_cat
attack_category
attack_subcat
is_executing_exploit
exploit
ground_truth
ground_truth_label
dataset_id
dataset_name
dataset_role
role
branch
source_format
source_file
source_file_name
source_file_path
source_file_hash
source_normalized_path
source_event_uid_refs
parser_run_id
parser_name
parser_version
schema_name
schema_version
normalized_artifact_id
feature_group
feature_schema_name
feature_schema_version
event_uid
sample_uid
entity_type
entity_id
window_start
window_end
window_size_seconds
window_step_seconds
scenario_name
raw_fields_json
metadata_json
created_at
```

Примечание: `model_ready_v1.json` сейчас не включает `entity_type`, `entity_id`, `window_start`, `window_end`, `window_size_seconds`, `window_step_seconds`, но `features/contracts.py` включает их в `X_EXCLUDED_COLUMNS`. Для X validation нужно использовать более строгий union.

##### Проверки LeakageChecker

Команда:

```bash
python manage.py stage-two run-leakage-checks
```

Проверки:

| Проверка | Условие отказа |
|---|---|
| `x_forbidden_columns` | forbidden X columns есть в model-ready X files и содержат non-null values |
| `test_absent_from_train` | `dataset_role='TEST'` найден в TRAIN model-ready files |
| `preprocessing_fit_only_train` | preprocessing artifact имеет `fitted_on_role != 'TRAIN'` |

Severity для failed leakage report: `CRITICAL`.

`block_model_ready_if_failed()` может пометить успешный model-ready artifact как `BLOCKED`, если leakage report завершился ошибкой.

##### Безопасный паттерн model-ready

Ожидаемое разделение artifacts:

```text
parquet/model_ready/tabular/{branch}/TRAIN/schema=v1/X_train.parquet
parquet/model_ready/labels/{branch}/TRAIN/schema=v1/y_train.parquet
parquet/model_ready/tabular/{branch}/VALIDATION/schema=v1/X_validation.parquet
parquet/model_ready/labels/{branch}/VALIDATION/schema=v1/y_validation.parquet
parquet/model_ready/tabular/{branch}/TEST/schema=v1/X_test.parquet
parquet/model_ready/labels/{branch}/TEST/schema=v1/y_test.parquet
```

X files содержат только model features. y files содержат labels. Traceability/source fields остаются в catalog и optional audit artifacts, а не в X.

##### Небезопасные предположения

- Не выводить `benign` из отсутствующего label.
- Не использовать filename labels для TEST.
- Не выполнять threshold tuning на TEST.
- Не смешивать role partitions в одном X artifact.
- Не хранить `source_file_path`/`event_uid`/`dataset_name` в X, потому что модели могут запомнить source identity.

---

### Источник: `docs/ru/code-documentation/dataset_contracts.md`

[Открыть исходный файл](ru/code-documentation/dataset_contracts.md)

#### Dataset-specific contracts

Этот документ суммирует группы датасетов из существующих Stage One analysis docs в `docs/ru/analysis-dataset`. Количества взяты из уже созданной документации Stage One; это не новый пересчет filesystem.

##### DNS TRAIN

| Формат | Файлов | Статус | Parser strategy | Labels |
|---|---:|---|---|---|
| `csv` | 8 | `PARTIALLY_SUPPORTED` | `DnsCsvParser` | filename/class hints: benign, malware, phishing, spam; non-TEST inference разрешен, но должен фиксироваться |
| `pcap` | 4 | `NEEDS_CUSTOM_PARSER` | `DnsPacketCaptureParser` | filename hints; parser отдает packet summaries |
| `pcap.csv` | 14 | `READY_FOR_FEATURE_EXTRACTION` | `DnsPcapCsvParser` | filename/class hints: audio, benign, compressed, exe, image, text, video |

Ограничения:

- Labels из filename являются inferred labels, а не embedded ground truth.
- Raw files остаются неизменными.
- Role path `TRAIN` используется только для training fit.

##### DNS VALIDATION

| Формат | Файлов | Статус | Parser strategy | Labels |
|---|---:|---|---|---|
| `pcap` | 5 | `NEEDS_CUSTOM_PARSER` | `DnsPacketCaptureParser` | filename hints: attack/benign; только validation |
| `txt` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `DnsTxtDomainListParser` для `VALIDATION` | partial; требуется явное class assignment |

Ограничения:

- VALIDATION может использоваться для model selection/early stopping в зависимости от дизайна эксперимента, но не для fit scalers/encoders, если политика требует TRAIN-only preprocessing fit.
- Хранить отдельно от TRAIN и TEST artifacts.

##### DNS TEST

| Формат | Файлов | Статус | Parser strategy | Labels |
|---|---:|---|---|---|
| `csv` | 1 | `PARTIALLY_SUPPORTED` | `DnsCsvParser`, поддержка TEST без header | sample содержит `label_or_flag`; только evaluation |
| `pcap` | 0 | `BROKEN_OR_EMPTY` | файлов нет |
| `pcap.csv` | 0 | `BROKEN_OR_EMPTY` | файлов нет |

Ограничения:

- TEST нельзя использовать для training, preprocessing fit, threshold tuning или feature selection.
- Filename heuristic отключен для TEST.

##### Host TRAIN

| Формат | Файлов | Статус | Parser strategy |
|---|---:|---|---|
| `csv` | 101 | `PARTIALLY_SUPPORTED` | `HostCsvParser` |
| `auth.log` | 23 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser`; registry покрывает log formats |
| `cpu.log` | 13 | `PARTIALLY_SUPPORTED` | `HostLineLogParser` / metric handling |
| `diskio.log` | 12 | `PARTIALLY_SUPPORTED` | `HostLineLogParser` / metric handling |
| `filesystem.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | line/metric parser |
| `fsstat.log` | 12 | `READY_FOR_FEATURE_EXTRACTION` | line/metric parser |
| `ghc` | 56158 | `NEEDS_CUSTOM_PARSER` | `HostSyscallTraceParser` |
| `info` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `journal` | 17 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `journal~` | 1 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `json` | 219 | `NEEDS_CUSTOM_PARSER` | `HostJsonLinesParser` |
| `json-1` | 1 | `READY_FOR_FEATURE_EXTRACTION` | `HostJsonLinesParser` |
| `log` | 98 | `NEEDS_CUSTOM_PARSER` | `HostLineLogParser` |
| `log-1`, `log-2`, `log-3` | 49 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `mainlog*`, `messages*`, `syslog*`, `mail-*` | 66 | в основном `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` |
| `netflow_ids` | 50 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` |
| `pcap` | 15 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` для TRAIN |
| `sc` | 210 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` |
| `txt` | 3170 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` |
| `xml` | 40 | `READY_FOR_FEATURE_EXTRACTION` | `HostXmlParser` |

Labels:

- `csv` имеет embedded normal/attack categories и binary labels.
- `cpu.log` имеет partial labels.
- многие telemetry/log/trace formats не имеют direct labels и требуют external mapping/window/scenario joins.
- отсутствие label остается `unlabeled`.

##### Host VALIDATION

| Формат | Файлов | Статус | Parser strategy | Labels/timestamp |
|---|---:|---|---|---|
| `cap` | 44 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | packet header timestamp; нужны external labels/scenario |
| `csv` | 6 | `READY_FOR_FEATURE_EXTRACTION` | `HostCsvParser` | `is_executing_exploit` |
| `json` | 130 | `READY_FOR_FEATURE_EXTRACTION` | `HostJsonLinesParser` | timestamp fields; external/scenario labels |
| `netflow_day` | 2 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` | time; direct labels отсутствуют |
| `pcap` | 1 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | packet timestamp; external labels |
| `pcapng` | 5 | `NEEDS_CUSTOM_PARSER` | `HostPacketCaptureParser` | enhanced packet timestamp; external labels |
| `txt` | 6495 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` | Time; direct labels отсутствуют |
| `wls_day` | 3 | `READY_FOR_FEATURE_EXTRACTION` | `HostNetflowParser` в текущем seed; JSON-lines semantics отмечены в analysis docs |

##### Host TEST

| Формат | Файлов | Статус | Parser strategy | Labels |
|---|---:|---|---|---|
| `bson` | 9005 | `NEEDS_CUSTOM_PARSER` | `HostBsonSandboxParser` для TEST | direct labels в sample отсутствуют; external labels, если есть |
| `csv` | 3 | `PARTIALLY_SUPPORTED` | `HostCsvParser` | отдельные label CSV maps; только TEST evaluation |
| `json` | 7071 | `NEEDS_CUSTOM_PARSER` | `HostJsonLinesParser` | TEST не используется для training; external labels |
| `log` | 4086 | `READY_FOR_FEATURE_EXTRACTION` | `HostLineLogParser` | external labels по умолчанию отсутствуют |
| `txt` | 274419 | `READY_FOR_FEATURE_EXTRACTION` | `HostSyscallTraceParser` | TEST не используется для training |

Ограничения:

- TEST artifacts можно нормализовать и оценивать, но нельзя использовать для любого fit/tuning.
- Filename heuristic отключен для TEST.
- Отдельные label files должны join-иться только для evaluation и должны сохранять `label_source`.

##### Ограничения групп датасетов

- Counts взяты из generated docs; их нужно обновлять после изменения filters или sorted tree.
- Некоторые статусы Stage One появились до более поздней реализации parser; для текущего runnable status использовать parser coverage.
- Большие counts для Host TEST `txt` и `bson` требуют memory-safe batching/splitting strategy.

---

### Источник: `docs/ru/code-documentation/extension_points.md`

[Открыть исходный файл](ru/code-documentation/extension_points.md)

#### Точки расширения

##### Добавить новый handler

Где менять:

- новый module в `scripts/handlers/<group>`;
- маршрут в `scripts/handlers/router_handler.py` или group router;
- config constants в `config.py`, если нужны пути.

Контракт:

- валидировать входные пути;
- возвращать dataclass result;
- писать JSON через `JsonDataManager`;
- не изменять raw-файлы;
- сохранять разделение TRAIN/VALIDATION/TEST.

Проверка:

```bash
python -m compileall -q manage.py config.py scripts
python manage.py handlers <service> <action>
```

Обновить документацию:

- this section;
- `cli_and_routing.md`;
- relevant Stage One docs.

##### Добавить action для `dns_analyze`

Где менять:

- добавить handler file в `scripts/handlers/dns_analyze`;
- экспортировать class в `scripts/handlers/dns_analyze/__init__.py`;
- добавить function в `run_action.py`;
- добавить route в `router_dns.py`.

Минимальный контракт:

- читать `sort-path-dns-file.json`;
- валидировать role/format bucket;
- анализировать ограниченную выборку файлов;
- писать summary JSON;
- писать RU/EN docs и reports;
- возвращать dataclass со status и paths.

##### Добавить action для `host_analyze`

Аналогично DNS, но файлы находятся в `scripts/handlers/host_analyze`, а маршрут добавляется в `router_host.py`.

Учитывайте смешанные схемы и большие файлы. Не загружайте файлы без ограничений целиком в память.

##### Добавить class парсера

Где менять:

- `scripts/stage_two/parsers/<module>.py`;
- при необходимости shared utilities в `parsers/common.py`, `csv_utils.py`, `json_utils.py`, `input_reader.py`.

Контракт:

- наследовать `BaseParser`;
- реализовать `parse()` и желательно потоковый `parse_batches()`;
- отдавать normalized events с обязательными fields;
- вызывать `self.validate_result(result)`;
- использовать `LabelResolverProtocol`;
- не синтезировать текущее время как source timestamp;
- хранить raw/source fields в `raw_fields_json` или `metadata_json`, а не в X features.

Проверки:

```bash
python -m pytest -q tests/stage_two/test_<parser>*.py
python -m pytest -q tests/stage_two/test_parser_registry_seed.py
```

##### Добавить запись parser registry

Где менять: `scripts/stage_two/parser_registry/parser_registry_seed.json`.

Шаги:

1. Добавить parser group или source format.
2. Запустить:

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
```

3. Проверить `is_active=true` в `parser_registry`.

##### Добавить version схемы

Где менять:

- `schemas/normalized`;
- `schemas/features`;
- `schemas/model_ready`;
- registry code, если требуется новое поведение layer.

Контракт:

- увеличить `schema_version`;
- явно зафиксировать стратегию backward compatibility;
- обновить регистрацию `schema_versions`;
- обновить writer/validator tests.

##### Добавить label mapping rule

Где менять:

- DB table `label_mapping_rules`; or
- `PATH_DATA_STORAGE/config/label_mapping_rules.json`.

Контракт:

- определить `rule_uid`;
- по возможности ограничить правило через branch/role/source_format;
- использовать явный `label_source`;
- задать `label_status` и confidence;
- не создавать TEST filename heuristic labels.

Проверяйте unit tests для `LabelResolver`.

##### Добавить quality check

Где менять: `scripts/stage_two/quality/checkers.py`.

Контракт:

- возвращать `QualityCheckResult`;
- включать severity;
- включать `rows_total`, `rows_failed` и diagnostic details;
- при необходимости регистрировать aggregate через `register_quality_report`.

Если check защищает от leakage, failed severity должен быть `CRITICAL`.

##### Добавить stage для feature/model-ready

Где менять:

- feature logic в `scripts/stage_two/features`;
- model-ready logic в `scripts/stage_two/model_ready`;
- CLI route в `scripts/stage_two/cli.py` только после появления реализации.

Контракт:

- хранить role partitions отдельно;
- сохранять traceability fields в feature layer;
- исключать forbidden columns из X;
- писать y отдельно;
- выполнять fit preprocessing только на TRAIN;
- регистрировать artifacts в catalog;
- запускать leakage checks перед использованием model-ready artifacts.

Проверки:

```bash
python -m pytest -q tests/stage_two/test_leakage_contracts.py
python manage.py stage-two run-leakage-checks
```

---

### Источник: `docs/ru/code-documentation/traceability.md`

[Открыть исходный файл](ru/code-documentation/traceability.md)

#### Трассируемость

Traceability связывает model-ready artifact с feature artifact, normalized Parquet, parser run, raw file и dataset.

##### Сервис

Файл: `scripts/stage_two/traceability/service.py`.

Команда:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Режимы поиска:

- числовой argument -> `model_ready_artifacts.id`;
- нечисловой argument -> `model_ready_artifacts.artifact_path`.

##### Цепочка

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

##### Возвращаемая metadata

`TraceabilityChain` возвращает dictionaries для:

- `model_ready_artifact`;
- `feature_artifact`;
- `normalized_artifact`;
- `parser_run`;
- `dataset_file`;
- `dataset`.

Ключевые fields включают artifact paths, role, branch, data type/modality, statuses, parser counters, raw file path/hash и dataset identity.

##### Обязательные связи

Сервис поднимает `TraceabilityError`, если:

- model-ready artifact не найден;
- `feature_artifact_id` равен null;
- связанный feature artifact не найден;
- `normalized_artifact_id` равен null;
- связанный normalized artifact не найден;
- связанный parser run не найден;
- связанный dataset file не найден;
- связанный dataset не найден.

##### Следствия контракта

Хотя некоторые FK columns nullable для поддержки staged/incomplete artifacts, production artifacts для экспериментов должны заполнять traceability links. Иначе:

- воспроизводимость нарушена;
- leakage audits не могут атрибутировать samples;
- academic implementation description не может доказать lineage;
- model-ready artifacts должны считаться incomplete.

##### Traceability в row schemas

Normalized rows включают event/file/parser fields. Feature rows должны сохранять:

```text
sample_uid
dataset_id
normalized_artifact_id
role
branch
feature_group
feature_schema_name
feature_schema_version
source_event_uid_refs
source_normalized_path
created_at
```

Эти traceability fields обязательны в feature artifacts, но исключаются из model-ready X artifacts. Они остаются в catalog и audit layers.

---

### Источник: `docs/ru/code-documentation/risks_and_technical_debt.md`

[Открыть исходный файл](ru/code-documentation/risks_and_technical_debt.md)

#### Риски, ограничения и technical debt

##### Известные ограничения

| Риск | Где возникает | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Fallback Host role в TEST | `HostDatasetHandler._detect_role` | файлы без role token попадут в TEST | проверить `host-path-file.json` | требовать явные role directories, добавить strict mode |
| Жестко заданный Host filter whitelist | `HostDatasetFilterHandler` | новые datasets/formats исключаются | причины в filter log | вынести rules в config с тестами |
| Статусы Stage One могут отставать от Stage Two parsers | analysis docs vs parser registry | формат помечен `NEEDS_CUSTOM_PARSER`, хотя parser уже есть | `parser-coverage` | обновлять analysis docs после parser work |
| Неполная orchestration feature/model-ready | `features/`, `model_ready/` services есть, full CLI отсутствует | нет полного e2e X/y build | ревью CLI routes | реализовать explicit build-feature/build-model-ready commands |

##### Gaps в parser layer

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Смешанные CSV schemas | DNS/Host CSV | failures при парсинге строк, partial artifacts | parser reports, `PARTIAL_SUCCESS` | schema-specific parsing, per-file schema hints |
| Смешанные JSON schemas | Host TRAIN/TEST JSON | failed rows или слабая нормализация | parser error samples | schema-aware dispatch и JSON flatten tests |
| Неоднозначность WLS/NetFlow | registry для `wls_day` использует `HostNetflowParser` | semantic mismatch, если WLS является JSON-lines | parser coverage + sample parse | выделить WLS parser или обновить registry |
| Производительность PCAP/PCAPNG | packet parser | медленная обработка, pressure на память/диск | runtime metrics, parser reports | packet sampling, `dns-only`, chunked streaming |
| Сложность BSON | sandbox BSON | descriptor/event mismatch | parser warnings | descriptor state tests, bounded raw previews |

##### Риски leakage

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Labels попали в X | feature/model-ready build | model напрямую учит target | `run-leakage-checks` | `validate_x_columns`, strict excluded list |
| Source identity в X | source paths/event ids | model запоминает dataset/file | проверка forbidden columns | хранить traceability только в catalog/audit |
| TEST используется для fit/tuning | preprocessing/model code | невалидная evaluation | preprocessing fit check, review | enforcing TRAIN-only fit и CI checks |
| Filename label inference для TEST | изменения label resolver | загрязнение evaluation | unit tests | сохранять `label_hints_allowed(TEST)=False` |

##### Риски labels

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Отсутствующий label трактуется как benign | downstream feature/model code | false negatives, contaminated labels | label distribution checks | сохранять `unlabeled` и фильтровать supervised samples |
| Weak labels используются как ground truth | IDS/scenario/filename | noisy training labels | проверять `label_status` | train/evaluate by label confidence/source |
| Conflicting labels игнорируются | resolver candidates | неверный target | counts по `conflicting_label` | блокировать или вручную разруливать conflicts |

##### Риски timestamp

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Missing timestamp заменен текущим временем | parser implementation | invalid temporal features | review `timestamp_type`, tests | использовать `timestamp=null`, `timestamp_type=missing/event_order` |
| Relative time трактуется как absolute | syscall/BSON/logs | неверный ordering/windows | parser tests | сохранять `timestamp_type=relative` и `event_index` |
| Смешанный timezone parsing | logs/json/csv | смещенные windows | sample validation | нормализовать в UTC только известные absolute timestamps |

##### Риски больших файлов

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Загрузка файла целиком | parsers/analyzers | исчерпание памяти | profiling, OOM | streaming readers, `parse_batches`, split-large-files |
| Слишком много Parquet parts | low max rows | filesystem overhead | artifact counts | настраивать `--max-output-part-rows` |
| Parallel workers на огромных файлах | `normalize-format --workers` | RAM/disk pressure | system monitoring | использовать workers=1, пока нет chunks |

##### Schema drift

| Риск | Где | Последствия | Как обнаружить | Как минимизировать |
|---|---|---|---|---|
| Source schema изменилась | datasets | parser failures | `PARTIAL_SUCCESS`, schema mismatch | сохранять schema hints, обновлять parser tests |
| Normalized schema развивается | schema JSON + parsers | downstream mismatch | DuckDB required column checks | версионировать schemas и поддерживать migrations |
| Feature schema mismatch | feature artifacts | model-ready invalid | quality checks | валидировать feature contract до регистрации |

##### Follow-up по technical debt

1. Добавить config-driven Host filter rules.
2. Добавить полный feature extraction CLI с traceability enforcement.
3. Добавить model-ready build CLI с automatic leakage gate.
4. Добавить отдельный WLS parser, если текущий netflow mapping семантически недостаточен.
5. Добавить schema-version registration для feature/model-ready schemas, а не только для normalized schema.
6. Добавить CI command для parser registry validation, leakage contract tests и docs link checks.

---

## Приложение: Project Proposal.docx

Источник: [`docs/ru/Project Proposal.docx`](<ru/Project Proposal.docx>).

> Ниже приведен текст, извлеченный из DOCX через OOXML. Визуальное форматирование Word не переносится в Markdown, но текстовые блоки и таблицы сохранены в порядке документа.

ИНДИВИДУАЛЬНОЕ ЗАДАНИЕ 2

ПРОЕКТНОЕ ПРЕДЛОЖЕНИЕ

| ФИО / TP номер | : | Джумаходжаева Малика / TP099270 |
| --- | --- | --- |
| Код набора | : | APUMF2508CYS(PR) |
| Код модуля | : | CT095-6-M-RMCE |
| Название модуля | : | Методология исследований в области вычислительной техники и инженерии |
| Преподаватель модуля | : | Dr. Murugananthan Velayutham |
| Назначенный научный руководитель | : | Dr. Jalil Md Desa |
| Название проекта | : | Поведенчески ориентированное гибридное обучение для обнаружения эксфильтрации данных |
| Дата выдачи | : | 6 февраля 2026 г. |
| Дата завершения | : | 24 апреля 2026 г. |

Аннотация

Эксфильтрация данных относится к числу наиболее серьезных и сложных угроз кибербезопасности, с которыми сталкиваются современные организации, поскольку она является скрытной, устойчивой и многоэтапной по своей природе. Традиционные системы обнаружения вторжений имеют существенные ограничения при выявлении сложных техник эксфильтрации, особенно тех, которые используют зашифрованные каналы связи, инсайдерские угрозы и продвинутые устойчивые угрозы. Хотя недавние исследования изучали подходы машинного и глубокого обучения для повышения возможностей обнаружения, большинство существующих систем используют одну модальность данных - либо сетевой трафик, либо телеметрию уровня хоста - и не моделируют последовательные поведенческие паттерны, характеризующие прогрессивные стадии атак эксфильтрации данных. В данном предложении представлена поведенчески ориентированная гибридная ML-архитектура, предназначенная для устранения этих ограничений путем интеграции хостовой телеметрии, анализа сетевого трафика и моделирования поведенческих последовательностей в единой архитектуре обнаружения. Предлагаемая архитектура объединит классические ансамблевые методы, такие как Random Forest и XGBoost, компоненты глубокого обучения CNN и LSTM-моделирование поведенческих последовательностей, чтобы выявлять как структурированные признаки, так и сложные временные зависимости в многoисточниковых данных безопасности. Архитектура также будет интегрирована с методом объяснимого искусственного интеллекта, а именно SHAP-атрибуцией признаков, для повышения интерпретируемости решений обнаружения и поддержки рабочих процессов аналитиков безопасности. Оценка архитектуры будет выполнена на публично доступных эталонных наборах данных по кибербезопасности с использованием стандартных классификационных метрик. Ожидается, что исследование внесет вклад в развитие гибридной архитектуры обнаружения, расширит существующие подходы, повысит способность раннего обнаружения скрытных многоэтапных атак эксфильтрации и предоставит воспроизводимые результаты для будущих исследований в области поведенческого обнаружения вторжений.

Ключевые слова: обнаружение эксфильтрации данных, гибридное глубокое обучение, CNN, моделирование поведенческих последовательностей, LSTM, объяснимый искусственный интеллект

Содержание

Список рисунков

Рисунок 1. Методология DSR	18

Рисунок 2. Диаграмма Ганта	23

Список таблиц

Таблица 1. Вехи проекта	23

Таблица 2. Оценка рисков	25

Список сокращений / терминология

| AUC | Площадь под ROC-кривой |
| --- | --- |
| CNN | Сверточная нейронная сеть |
| DL | Глубокое обучение |
| DNS | Система доменных имен |
| DSR | Исследование проектной науки |
| GCN | Графовая сверточная сеть |
| HTTPS | Защищенный протокол передачи гипертекста |
| IDS | Система обнаружения вторжений |
| LIME | Локальные интерпретируемые модельно-независимые объяснения |
| LSTM | Долгая краткосрочная память |
| ML | Машинное обучение |
| RNN | Рекуррентная нейронная сеть |
| ROC | Рабочая характеристика приемника |
| SHAP | Аддитивные объяснения Шепли |
| TLS | Безопасность транспортного уровня |
| XAI | Объяснимый искусственный интеллект |
| XGBoost | Экстремальный градиентный бустинг |

1. Введение

Быстрый рост цифровой инфраструктуры существенно изменил способы управления информацией и ее обмена в организациях. Большие объемы чувствительной информации передаются через облачные системы, корпоративные сети и персональные конечные устройства, которые стали основными средами обмена данными. Эти достижения дают значительные преимущества, однако они также создали новые сложные проблемы безопасности, требующие более совершенных технологий обнаружения.

Сегодня одной из наиболее серьезных угроз для организаций является эксфильтрация данных - несанкционированная передача чувствительной информации из внутренних систем во внешние пункты назначения, контролируемые злоумышленником. В отличие от многих других кибератак, которые часто обнаруживаются сразу, эксфильтрация данных обычно является скрытной, устойчивой и слабо заметной на начальных стадиях (Hozouri et al., 2025). Злоумышленники используют действительные учетные данные, зашифрованные каналы связи и протоколы вроде DNS-туннелирование, чтобы незаметно выводить чувствительные данные из корпоративных систем в течение длительного времени (Kamal & Mashaly, 2025).

Традиционные системы обнаружения вторжений, в основном опирающиеся на сигнатурные правила и заранее заданные шаблоны трафика, демонстрируют существенные ограничения при выявлении таких сложных и адаптивных угроз. В ответ на это недавние исследования все чаще рассматривают методы машинного обучения (ML) и глубокого обучения (DL) как более адаптивные альтернативы, способные выявлять аномальные паттерны в сетевых потоках, системных журналах и поведении пользователей (Chinnasamy et al., 2025). Однако большинство существующих подходов анализируют либо сетевой трафик, либо поведение хоста изолированно, что ограничивает их способность моделировать полную поведенческую последовательность многоэтапных атак эксфильтрации (Hozouri et al., 2025; Kamal & Mashaly, 2025).

В данном отчете представлено предложение исследования, направленного на устранение этих ограничений путем разработки поведенчески ориентированной гибридной архитектуры машинного обучения для обнаружения эксфильтрации данных. Предлагаемая архитектура объединяет хостовую телеметрию, анализ сетевого трафика и моделирование поведенческих последовательностей, чтобы обеспечить более полные возможности обнаружения сложных атак эксфильтрации.

2. Обзор предметной области

Эксфильтрация данных стала одной из наиболее значимых проблем современной кибербезопасности из-за растущей зависимости от цифровых систем для хранения и обработки чувствительных организационных данных. Эксфильтрация данных определяется как незаконное перемещение чувствительных данных из внутренней системы во внешнее место, контролируемое злоумышленником. Она часто связана с понятием продвинутых устойчивых угроз (APT), при которых злоумышленники получают скрытый и длительный доступ к скомпрометированным системам и систематически похищают ценную информацию (Kamal & Mashaly, 2025). Многоэтапное выполнение таких атак, включающее разведку, повышение привилегий, сбор данных, подготовку и финальную эксфильтрацию, затрудняет их раннее обнаружение, особенно традиционными системами безопасности (Hakim et al., 2024).

Злоумышленники используют различные методы маскировки эксфильтрации в обычном сетевом трафике. Распространенные техники включают DNS-туннелирование, утечку данных через HTTPS, злоупотребление облачными хранилищами и использование командно-контрольных каналов (C2) (Hozouri et al., 2025). Использование зашифрованных протоколов связи (TLS, HTTPS и DNS-over-HTTPS) дополнительно усложняет обнаружение, поскольку большинство систем безопасности ограничены анализом метаданных трафика (размер пакетов, время, частота коммуникаций и т. д.), а не содержимого полезной нагрузки (Chen et al., 2024). Кроме того, важным способом эксфильтрации являются инсайдерские угрозы, когда сотрудники с авторизованным доступом намеренно или непреднамеренно используются для раскрытия чувствительной информации организации (Ofori et al., 2025).

Сигнатурные и rule-based механизмы традиционно применялись в системах обнаружения вторжений для выявления известных шаблонов атак. Однако исследования, сравнивающие популярные IDS-решения, такие как Snort и Suricata, показывают, что в настройках по умолчанию они не выявляют сложные техники эксфильтрации, например ICMP-туннелирование (Qutqut et al., 2026). Эти результаты показывают, что сигнатурные методы не могут использоваться как единственный способ противодействия развивающимся угрозам безопасности.

Для устранения этих слабых мест методы машинного и глубокого обучения стали одним из основных направлений исследований в обнаружении киберугроз. Широко применяемые классические алгоритмы, включая Random Forest, Decision Trees и Gradient Boosting, показали сильные результаты в классификации структурированных признаков. В частности, ансамблевые методы на основе деревьев достигали точности выше 99% при обнаружении DNS-based эксфильтрации данных (Açıkgözoğlu, 2024; Thomas et al., 2025). Использование подходов глубокого обучения, включая CNN, RNN и Transformers, расширило возможности обнаружения за счет извлечения сложных временных и пространственных признаков из крупномасштабного сетевого трафика и поведенческих журналов (Kuppuraju et al., 2025).

Помимо анализа на сетевом уровне, все больший исследовательский интерес получает хостовые поведенческое обнаружение. Хостовые модели позволяют подробно видеть поведение пользователя и системы через анализ трасс системных вызовов, паттернов доступа к файлам, журналов выполнения процессов и пользовательской активности, которые не наблюдаются сетевыми методами. Недавние исследования показывают, что добавление контекстных и ролевых поведенческих признаков в модели обнаружения позволяет достигать точности 94-99% при снижении числа ложных срабатываний (Balogun et al., 2025). Autoencoders, один из типов моделей глубокого обучения, также показали эффективность при выявлении скрытой эксфильтрации данных в контейнеризованных средах с использованием на основе системных вызовов поведенческого мониторинга (Zuppelli et al., 2024).

Гибридные архитектуры обнаружения стали перспективным направлением, которое стремится объединить дополняющие сильные стороны разных аналитических методов и источников данных. Архитектуры, интегрирующие классическое машинное обучение с моделями глубокого обучения, например CNN-LSTM конвейерs и ансамблевые tree models, демонстрировали более высокую точность и устойчивость по сравнению с одно-модельными подходами (Cai et al., 2025; Potluri, 2024). В более поздних работах отбор признаков на основе reinforcement learning сочетался с XAI-методами для повышения возможностей обнаружения и интерпретируемости моделей в зашифрованном сетевом трафике (Sammour et al., 2026; Hanintya et al., 2025).

Несмотря на этот прогресс, в литературе сохраняется существенный пробел. Большинство предложенных систем обнаружения продолжает работать с одной модальностью данных - либо сетевым трафиком, либо хостовой телеметрией - и не моделирует явно поведенческие последовательности, которые предшествуют и составляют многоэтапные атаки эксфильтрации данных (Hozouri et al., 2025; Kamal & Mashaly, 2025). Этот пробел обосновывает разработку интегрированной поведенчески ориентированной архитектуры обнаружения, которая подробно рассматривается в постановке проблемы.

3. Постановка проблемы

Несмотря на значительные достижения в обнаружении вторжений на основе машинного и глубокого обучения, существующие системы обнаружения эксфильтрации данных остаются фундаментально ограниченными из-за неспособности интегрировать многoисточниковую поведенческую телеметрию и моделировать последовательные стадии сложных атак эксфильтрации.

Существующие подходы к обнаружению можно в целом разделить на сетевые и хостовые системы; обе дают лишь частичный взгляд на жизненный цикл атаки эксфильтрации. Сетевые системы анализируют потоки трафика, метаданные пакетов и характеристики DNS-запросов для выявления аномальных коммуникаций. Хотя эти методы показывали сильные статистические результаты - ансамблевые классификаторы достигали показателей обнаружения выше 99% в контролируемых условиях (Thomas et al., 2025; Açıkgözoğlu, 2024), - они не дают представления о действиях на уровне хоста и поведении пользователя. Следовательно, подозрительная сетевая активность не может быть надежно связана с действиями пользователя или процессами приложения, что затрудняет восстановление цепочки событий, завершившейся эксфильтрацией данных. Кроме того, широкое распространение HTTPS, TLS и DNS-over-HTTPS (DoH) ограничивает полезность на основе полезной нагрузки признаков. Это вынуждает сетевые системы использовать метаданные, которые не всегда эффективно разделяют нормальный и вредоносный зашифрованный трафик (Chen et al., 2024; Sammour et al., 2026).

Хостовые системы поведенческого обнаружения частично устраняют эти ограничения, предоставляя подробную видимость пользовательских действий, системных процессов и паттернов доступа к файлам. Эти подходы доказали эффективность для обнаружения инсайдерских угроз и поведенческих аномалий, особенно при включении контекстных и ролевых признаков в модели обнаружения (Balogun et al., 2025; Singh & Siddalingaiah, 2025). Однако только хостовые системы не могут напрямую наблюдать сетевую стадию эксфильтрации, когда чувствительные данные передаются во внешние пункты назначения, контролируемые злоумышленником. Без интеграции с сетевой телеметрией хостовые модели могут выявлять подозрительное поведение, но не могут подтвердить факт фактической эксфильтрации данных (Zuppelli et al., 2024).

Гибридные архитектуры обнаружения пытались закрыть этот пробел, объединяя разные методы машинного обучения и источники данных. Тем не менее большинство современных гибридных систем на практике остается одномодальным: часть из них использует либо сетевой трафик, либо хостовую телеметрию вместо реального объединения обоих источников (Cai et al., 2025; Potluri, 2024). Наиболее важно, что большинство гибридных решений основано на классификации аномалий на уровне отдельных журналов и не моделирует явно последовательности поведения, характерные для прогрессивных стадий многоэтапных атак эксфильтрации. Фреймворк ARKAIV, предложенный Hakim et al. (2024), является одной из немногих попыток прогнозировать эксфильтрационное поведение путем сопоставления системных журналов с тактиками MITRE ATT&CK, однако он опирается на один источник данных и обучения с учителем learning на размеченных наборах данных. Поэтому его применимость ограничена реальными средами, где размеченные данные о компрометациях встречаются редко.

Кроме того, хотя методы объяснимого ИИ, такие как SHAP и LIME, включались в системы обнаружения для повышения интерпретируемости моделей, существующие системы в основном предоставляют post-hoc объяснения важности признаков, а не пытаются восстановить поведенческую последовательность атаки (Hanintya et al., 2025). Это ограничивает их практическую полезность при расследовании инцидентов и проактивном реагировании на угрозы.

В совокупности эти ограничения показывают, что современные модели обнаружения в значительной степени реактивны и имеют узкую область охвата. Существует критический пробел в обнаружении скрытных многоэтапных атак эксфильтрации данных, которые охватывают как хостовое, так и сетевое пространство. Следовательно, требуется интегрированная архитектура обнаружения, объединяющая хостовую телеметрию, анализ сетевого трафика и моделирование поведенческих последовательностей в гибридной ML-архитектуре, чтобы обеспечить более точное, своевременное и комплексное обнаружение продвинутых атак эксфильтрации данных.

4. Исследовательские вопросы

На основе ограничений, выявленных в постановке проблемы, данное исследование отвечает на следующие вопросы:

Какие ключевые поведенческие индикаторы и признаки многoисточниковой телеметрии характеризуют прогрессивные стадии атак эксфильтрации данных в хостовых и сетевых средах?

Этот вопрос закрывает пробел в интегрированном анализе между хостовым и сетевым доменами путем определения полного набора признаков, описывающих жизненный цикл атак эксфильтрации данных.

Как можно эффективно объединить классические методы машинного обучения и методы глубокого обучения в гибридной архитектуре для повышения точности и устойчивости обнаружения?

Этот вопрос рассматривает, как гибридные подходы могут использовать взаимодополняющие сильные стороны разных парадигм обучения для повышения качества обнаружения на многoисточниковых данных.

Как можно встроить моделирование поведенческих последовательностей в гибридную архитектуру обнаружения для выявления паттернов многоэтапных атак эксфильтрации данных?

Этот вопрос направлен на устранение ограничения event-level обнаружения путем учета временных связей между видами поведения.

В какой степени методы объяснимого искусственного интеллекта могут повысить интерпретируемость решений обнаружения и поддержать расследование инцидентов?

Этот вопрос изучает, как интерпретируемость может повысить практическую применимость систем обнаружения в реальных операциях безопасности.

5. Цель и задачи

5.1 Цель

Основная цель данного исследования - спроектировать и оценить поведенчески ориентированную гибридную архитектуру машинного обучения, которая интегрирует хостовую телеметрию, анализ сетевого трафика и моделирование поведенческих последовательностей для улучшения обнаружения сложных многоэтапных атак эксфильтрации данных.

5.2 Задачи

Выявить и проанализировать ключевые поведенческие индикаторы и признаки многoисточниковой телеметрии, характеризующие прогрессивные стадии атак эксфильтрации данных в хостовых и сетевых средах, опираясь на доступные наборы данных и определения признаков из литературы.

Спроектировать и реализовать гибридную архитектуру машинного и глубокого обучения, объединяющую классические и глубокого обучения методы для классификации многoисточниковых поведенческих данных.

Разработать и интегрировать компонент моделирования поведенческих последовательностей в гибридную архитектуру, чтобы обеспечить обнаружение паттернов многоэтапных атак эксфильтрации данных.

Интегрировать методы объяснимого искусственного интеллекта в предлагаемую архитектуру и оценить их эффективность в повышении интерпретируемости решений обнаружения.

6. Область исследования

Этот раздел определяет границы предлагаемого исследования и уточняет, в какой степени архитектура будет разработана и оценена. Для обеспечения реализуемости в рамках 12-недельного проекта исследование будет сосредоточено на сочетании классических моделей машинного обучения (Random Forest и XGBoost) и моделей глубокого обучения (CNN и LSTM). Более сложные расширения, такие как graph-based neural networks, reinforcement learning компоненты и масштабное multi-dataset объединение, исключены из реализации и рассматриваются как направления будущей работы.

6.1 Фокус обнаружения

Исследование сосредоточено на обнаружении атак эксфильтрации данных в корпоративных сетевых средах. Предлагаемая архитектура будет ориентирована на многоэтапные сценарии эксфильтрации, включая сценарии, связанные с продвинутыми устойчивыми угрозами (APT), инсайдерскими угрозами и злоупотреблением скрытыми каналами связи, такими как DNS-туннелирование и зашифрованная через HTTPS эксфильтрация.

6.2 Источники данных

Предлагаемая архитектура объединит две основные категории телеметрии безопасности: поведенческие данные уровня хоста и данные сетевого трафика. Данные уровня хоста включают журналы системных вызовов, записи выполнения процессов, события доступа к файлам и журналы пользовательской активности. Сетевые данные включают признаки потоков трафика, метаданные пакетов, характеристики DNS-запросов и записи NetFlow. Сетевые наборы данных будут основным источником для обучения модели, тогда как хостовые поведенческие признаки будут включаться из совместимых наборов данных либо через симуляцию на уровне признаков, если парные наборы данных недоступны. Следовательно, интеграция будет происходить на уровне представления признаков, а не через прямое слияние сырых данных. Это осознанное ограничение области исследования, соответствующее 12-недельному графику, и оно не снижает валидность архитектуры многoисточниковой интеграции.

6.3 Методы машинного обучения

Исследование изучит интеграцию классических алгоритмов машинного обучения, в частности ансамблевых методов Random Forest и XGBoost, с CNN и на основе LSTM моделированием последовательностей. Объем исследования глубокого обучения ограничен доступными вычислительными ресурсами и временными рамками проекта. Методы reinforcement learning считаются вне области текущего исследования, хотя их потенциальная интеграция признается направлением будущих исследований.

6.4 Моделирование поведенческих последовательностей

Компонент моделирования поведенческих последовательностей будет сосредоточен на моделировании временных связей между хостовыми и сетевыми поведенческими событиями для выявления прогрессивных многоэтапных паттернов эксфильтрации. Область моделирования последовательностей ограничена обучения с учителем и полууправляемых подходами с использованием доступных размеченных наборов данных. Полностью обучения без учителя моделирование последовательностей, хотя и признается ценным направлением будущей работы, выходит за рамки данного исследования с учетом ограничений доступной разметки и оценочных эталонные наборы данных.

6.5 Объяснимость

Компонент объяснимости будет сосредоточен на интеграции на основе SHAP методов атрибуции признаков для предоставления интерпретируемых объяснений решений обнаружения. Область объяснимости ограничена генерацией объяснений после обнаружения. Практическая оценка объяснимости будет проводиться по качеству атрибуции признаков и ее потенциальной полезности для поддержки рабочих процессов аналитиков безопасности.

6.6 Оценка

Оценка предлагаемой архитектуры будет проводиться в контролируемых экспериментальных условиях с использованием публично доступных эталонные наборы данных. Для оценки производительности архитектуры будут использоваться стандартные классификационные метрики: accuracy, precision, recall, F1-score и площадь под ROC-кривой (AUC).

6.7 Географическая и организационная область

Исследование не ограничено конкретным географическим регионом или отраслевым сектором. Предлагаемая архитектура разработана как универсальное решение обнаружения, применимое к корпоративным средам в широком смысле.

7. Значимость исследования

Этот раздел объясняет, почему предлагаемое исследование является значимым и какой вклад оно может внести в области кибербезопасности и машинного обучения.

7.1 Решение критически важной проблемы кибербезопасности

Эксфильтрация данных является одной из наиболее финансово и операционно разрушительных кибератак. Последствия успешной эксфильтрации включают не только немедленные финансовые потери, но и регуляторные штрафы, репутационный ущерб и долгосрочный вред конкурентоспособности. Скрытный и устойчивый характер таких атак означает, что организации часто длительное время не знают о продолжающихся компрометациях (Hozouri et al., 2025). Поэтому разработка более сильного и комплексного подхода к обнаружению имеет практическую значимость для организаций, использующих цифровую инфраструктуру в своей деятельности.

7.2 Развитие современного уровня архитектур обнаружения

С академической точки зрения предлагаемое исследование напрямую вносит вклад в литературу по обнаружению вторжений на основе машинного обучения, закрывая четко определенный и обоснованный исследовательский пробел. Как показано в обзоре литературы и постановке проблемы, большинство современных систем обнаружения являются одномодальными и не моделируют поведенческие последовательности многоэтапных атак эксфильтрации (Kamal & Mashaly, 2025; Hozouri et al., 2025). Предлагаемая поведенчески ориентированная гибридная архитектура расширяет существующие гибридные подходы, объединяя хостовую телеметрию, анализ сетевого трафика и моделирование поведенческих последовательностей в единой архитектуре обнаружения, что остается недостаточно изученной практикой в литературе.

7.3 Улучшение раннего обнаружения многоэтапных атак

Особенно значимым вкладом предлагаемого исследования является акцент на раннем обнаружении через моделирование поведенческих последовательностей. Существующие механизмы обнаружения в основном реактивны и выявляют эксфильтрацию, когда передача уже началась (Hakim et al., 2024). Предлагаемая архитектура стремится обеспечить более раннее обнаружение эксфильтрации путем моделирования последовательных поведенческих паттернов, ведущих к финальной стадии эксфильтрации, например разведки, латерального перемещения и подготовки данных. Это сокращает dwell time злоумышленника и минимизирует объем данных, который может быть выведен до обнаружения. Такая способность имеет прямую операционную значимость для команд безопасности, отвечающих за обнаружение и реагирование на инциденты.

7.4 Поддержка исследовательского сообщества кибербезопасности

Предлагаемое исследование внесет вклад в исследовательское сообщество кибербезопасности за счет систематической оценки предлагаемой архитектуры. Исследование предоставит воспроизводимые результаты, которые другие исследователи смогут расширить благодаря подробному описанию экспериментов и сравнению качества с представительными современными лучшими базовыми подходами. Кроме того, выявление и анализ междоменных поведенческих признаков, определяющих многоэтапные атаки эксфильтрации, может стать полезной основой для будущих исследований поведенческого обнаружения угроз, разработки наборов данных и проектирования threat intelligence frameworks.

8. Методология исследования

Этот раздел описывает методологию исследования, которая будет использоваться для достижения цели и задач данной работы.

8.1 Дизайн исследования и подход

Исследование будет использовать количественную методологию design science research (DSR). DSR особенно подходит для исследований в computing and engineering, направленных на создание и оценку нового артефакта - в данном случае поведенчески ориентированной гибридной ML-архитектуры - как решения выявленной практической проблемы (Hevner et al., 2004). Методология DSR включает итеративные циклы проектирования, реализации и оценки, что соответствует цели разработки и улучшения архитектуры обнаружения через систематические эксперименты. Исследование будет следовать структурированной пятифазной методологии, показанной на рисунке 1.

Рисунок 1. Методология DSR

8.2 Фаза 1: выявление признаков и подготовка набора данных

Первая фаза соответствует задаче 1 и сосредоточена на систематическом выявлении поведенческих индикаторов и признаков многoисточниковой телеметрии, которые характеризуют прогрессивные стадии атак эксфильтрации данных.

8.2.1 Выбор набора данных

Исследование будет использовать публично доступные наборы данных по кибербезопасности, которые содержат хостовую или сетевую телеметрию безопасности. Признается, что большинство публичных наборов данных предоставляет сетевую или хостовую телеметрию независимо. Поэтому исследование будет сосредоточено на интеграции признаков, полученных из разных источников, в единое представление для имитации многoисточникового поведенческого анализа.

8.2.2 Инжиниринг признаков

Инжиниринг признаков будет включать извлечение и конструирование признаков из хостовых и сетевых источников данных. Сетевые признаки будут включать статистики потоков трафика, распределения размеров пакетов, интервалы между событиями, энтропию DNS-запросов и метрики частоты коммуникаций. Хостовые признаки будут включать распределения частоты системных вызовов, энтропию доступа к файлам, паттерны выполнения процессов и индикаторы использования привилегий. Кроме того, сопоставления с тактиками MITRE ATT&CK будут использоваться как промежуточный слой для выравнивания извлеченных признаков с известными индикаторами стадий атаки по подходу Hakim et al. (2024). Анализ важности признаков будет выполняться с использованием SHAP values для выявления наиболее влиятельных поведенческих индикаторов, вносящих вклад в качество обнаружения. Это поддержит валидацию выбранных признаков и их релевантность разным стадиям атак эксфильтрации данных.

8.3 Фаза 2: проектирование гибридной архитектуры

Вторая фаза соответствует задаче 2 и включает проектирование гибридной архитектуры машинного и глубокого обучения.

8.3.1 Архитектура фреймворка

В предлагаемой архитектуре будут три основных компонента, работающих в интегрированном конвейер:

Слой интеграции многoисточниковых данных будет принимать, предобрабатывать и нормализовать хостовую телеметрию и сетевой трафик из разных источников в единое представление признаков, пригодное для последующих компонентов моделирования.

Гибридный слой классификации ML/DL будет применять ансамблевые методы (Random Forest и XGBoost) и глубокого обучения (CNN) для классификации отдельных событий и образцов трафика как легитимный или вредоносный на основе структурированных представлений признаков.

Слой моделирования поведенческих последовательностей будет отвечать за моделирование временных связей между последовательными поведенческими событиями для выявления паттернов многоэтапных атак; он будет реализован с использованием LSTM-подхода глубокого обучения.

Выходы компонентов классификации и моделирования последовательностей будут объединяться с использованием late fusion подхода, при котором вероятности предсказаний обоих компонентов агрегируются для получения финального классификационного решения. Такой дизайн соответствует установленному принципу, согласно которому гибридные архитектуры, объединяющие классические и глубокого обучения методы, могут повышать точность и способность к обобщению по сравнению с одномодельными подходами (Almuhanna & Dardouri, 2025).

8.4 Фаза 3: моделирование поведенческих последовательностей

Третья фаза соответствует задаче 3 и сосредоточена на разработке компонента моделирования поведенческих последовательностей.

Моделирование поведенческих последовательностей будет реализовано с использованием сетей Long Short-Term Memory (LSTM), хорошо подходящих для изучения временных зависимостей в последовательных данных событий (Yumlembam et al., 2025). Компонент моделирования последовательностей будет получать на вход упорядоченные последовательности поведенческих событий, полученные из хостовой и сетевой телеметрии, и обучаться выявлять паттерны, указывающие на прогрессивное многоэтапное атакующее поведение. Последовательности событий будут строиться путем агрегирования упорядоченных по времени векторов признаков в скользящих временных окнах, что позволит модели фиксировать как краткосрочные, так и среднесрочные поведенческие паттерны.

Последовательности будут формироваться с использованием скользящих временных окон над упорядоченными потоками событий. Каждая последовательность будет состоять из фиксированного числа событий (например, 50-100 событий на последовательность), а метки будут назначаться на основе наличия эксфильтрационной активности внутри окна последовательности. Модель будет выполнять бинарную классификацию на уровне последовательности (легитимный vs exfiltration).

8.5 Фаза 4: интеграция объяснимости

Четвертая фаза соответствует задаче 4 и включает интеграцию методов объяснимого искусственного интеллекта в предлагаемую архитектуру.

Основной техникой объяснимости будет SHAP (SHapley Additive exPlanations), что соответствует выводам Hanintya et al. (2025), где показано, что SHAP предоставляет наиболее детальные глобальные и локальные объяснения среди XAI-методов при применении к обнаружению вторжений. Эффективность объяснимости будет оцениваться качественно и количественно. Качественно на основе SHAP объяснения будут анализироваться для заданного набора выбранных случаев обнаружения, а именно репрезентативной выборки истинно положительных случаев и ложно положительных случаев из каждого фолд кросс-валидации, чтобы оценить, дают ли сформированные объяснения полезное понимание поведенческих паттернов, ведущих к решениям классификации, и согласуются ли они с известными индикаторами стадий атак, описанными в MITRE ATT&CK. Количественно будет измеряться согласованность ранжирования SHAP-признаков между фолдами кросс-валидации для оценки стабильности и устойчивости объяснений при разных распределениях данных. Высокая согласованность означает, что объяснения отражают реальные изученные паттерны, а не артефакты конкретных разбиений данных.

8.6 Фаза 5: оценка и валидация

Пятая фаза будет включать систематическую экспериментальную оценку предлагаемой архитектуры.

8.6.1 Метрики оценки

Для определения производительности архитектуры будут использоваться стандартные классификационные метрики: accuracy, precision, recall, F1-score, false positive rate (FPR) и площадь под ROC-кривой (AUC). Поскольку дисбаланс классов часто характерен для данных кибербезопасности, то есть объем легитимный трафик значительно превышает объем вредоносных образцов, precision, recall и F1-score будут рассматриваться как основные метрики качества, а AUC - как показатель общей дискриминативной способности.

Для оценки эффективности предлагаемой гибридной архитектуры будут выполнены два уровня сравнения. Во-первых, ablation study сравнит полную гибридную архитектуру с ее отдельными компонентами, чтобы оценить вклад каждого архитектурного слоя в общее качество обнаружения. Во-вторых, если наборы данных пересекаются с ранее опубликованными работами, результаты будут сопоставлены с сравнимыми современными лучшими подходами (например, Cai et al., 2025; Chen et al., 2024), чтобы поместить результаты в контекст существующей литературы. Такой двойной подход к сравнению обеспечивает строгую оценку как внутренних проектных решений, так и внешнего исследовательского вклада архитектуры.

Оценка будет проводиться с использованием stratified k-фолд кросс-валидации для обеспечения устойчивости и обобщаемости результатов при разных распределениях данных.

8.6.2 Этические аспекты

Поскольку исследование будет основано исключительно на публично доступных эталонных данных, персонально идентифицируемая информация не будет собираться или обрабатываться. Наборы данных, используемые в исследовании, предоставлены их авторами для академических исследований. Захват live network traffic проводиться не будет, и реальные организационные системы не будут использоваться или мониториться. Следовательно, исследование имеет низкий риск этических проблем и не требует дополнительного этического одобрения.

9. План исследования

В этом разделе представлен график и расписание предлагаемого исследования.

9.1 Обзор исследовательского графика

Исследование запланировано на 12 недель с мая 2026 года по август 2026 года. График организован вокруг пяти методологических фаз, определенных в разделе 8. Рисунок 2 представляет подробный исследовательский график в виде диаграммы Ганта. Задачи организованы по фазам и сопоставлены с календарем проекта по неделям.

Рисунок 2. Диаграмма Ганта

9.2 Описание фаз и ключевые вехи

Исследование организовано в пять методологических фаз, каждая из которых имеет определенные результаты и вехи. Таблица 1 обобщает ключевые вехи, результаты и критерии успеха для каждой фазы исследования.

Таблица 1. Вехи проекта

| Фаза | Веха | Ключевой результат | Критерий успеха | Целевая дата |
| --- | --- | --- | --- | --- |
| Фаза 1 - выявление признаков и подготовка набора данных | Наборы данных доступны, признаки извлечены | Предобработанный набор признаков с сопоставлениями MITRE ATT&CK | Все наборы данных загружены, очищены и обработаны; набор признаков задокументирован | 15 мая |
| Фаза 2 - проектирование гибридной архитектуры | Функциональный classification конвейер реализован | Прототип гибридной архитектуры обнаружения | Архитектура достигает базовый подход-качества классификации как минимум на одном наборе данных | 12 июня |
| Фаза 3 - моделирование поведенческих последовательностей | LSTM-модель последовательностей интегрирована в архитектуру | Интегрированный LSTM-компонент моделирования последовательностей | Модель фиксирует временные последовательности событий в хостовой и сетевой телеметрии; интегрированный выход поступает в ансамблевый слой | 3 июля |
| Фаза 4 - интеграция объяснимости | SHAP-модуль интегрирован и формирует выходы | SHAP-модуль объяснений с sequence-aware атрибуцией | SHAP values сформированы для отдельных решений обнаружения; объяснения проверены по известным последовательностям атак | 24 июля |
| Фаза 5 - оценка и валидация | Все эксперименты завершены, результаты задокументированы | Отчет об экспериментальных результатах с сравнительным анализом | Архитектура превосходит как минимум один базовый подход по F1-score и AUC на фолдами кросс-валидации; ablation study завершен | 14 августа |
| Написание отчета | Финальный отчет отправлен | Завершенный исследовательский отчет и слайды | Отчет соответствует требованиям сдачи; все разделы финализированы и вычитаны | 28 августа |

9.2.1 Фаза 1 - выявление признаков и подготовка набора данных

Эта фаза включает систематический обзор литературы для выявления поведенческих индикаторов, выбор и доступ к эталонные наборы данных, инжиниринг признаков из хостовой и сетевой телеметрии, а также сопоставление с тактиками MITRE ATT&CK. Ключевой вехой этой фазы является финализированный набор признаков и предобработанный набор данных, готовый к моделированию. Результатом является документированный отчет по инжинирингу признаков.

9.2.2 Фаза 2 - проектирование и реализация гибридной архитектуры

Эта фаза включает проектирование слоя многoисточниковой интеграции и гибридной ML/DL архитектуры классификации, реализацию компонентов фреймворка и разработку базовых моделей для сравнения. Ключевая веха - функциональный прототип гибридной архитектуры классификации. Результатом является реализованный и протестированный classification конвейер.

9.2.3 Фаза 3 - моделирование поведенческих последовательностей

Эта фаза включает разработку на основе LSTM компонента моделирования последовательностей и интеграцию слоя моделирования последовательностей в более широкую гибридную архитектуру. Ключевая веха - полностью интегрированная архитектура с возможностью моделирования поведенческих последовательностей.

9.2.4 Фаза 4 - интеграция объяснимости

Эта фаза включает интеграцию на основе SHAP объяснимости в архитектуру и проектирование sequence-aware выходов объяснения. Ключевая веха - функциональный модуль объяснимости, формирующий интерпретируемые результаты обнаружения.

9.2.5 Фаза 5 - оценка и валидация

Эта фаза включает эксперименты кросс-валидации, ablation studies для оценки вклада отдельных компонентов архитектуры, внешнее сравнение с современными лучшими подходами (например, Cai et al., 2025; Chen et al., 2024) и оценку cross-dataset generalizability. Ключевая веха - полный набор экспериментальных результатов с сравнительным анализом.

9.2.6 Написание отчета и подготовка к защите (постоянно)

Включает непрерывное написание глав в течение исследовательского процесса, проверку и доработку финального черновика, подготовку к устной защите и финальную отправку в августе 2026 года.

9.3 Планирование рисков и мер реагирования

Таблица 2 обобщает ключевые риски, выявленные для данного исследования, и соответствующие меры реагирования.

Таблица 2. Оценка рисков

| Риск | Вероятность | Влияние | Митигирующая мера |
| --- | --- | --- | --- |
| Несовместимость наборов данных между хостовыми и сетевыми источниками | Средняя | Высокое | Использовать на уровне признаков integration и синтетическую симуляцию поведения хоста для согласования неоднородных наборов данных |
| Ограничения вычислительных ресурсов для обучения глубокого обучения моделей | Средняя | Среднее | Использовать облачные вычислительные ресурсы (например, Google Colab, Kaggle); оптимизировать сложность модели |
| Недостаточное качество компонента моделирования последовательностей | Низкая | Среднее | Перейти к более простым temporal aggregation features; скорректировать область задачи O3 |
| Задержки графика из-за сложности интеграции | Средняя | Среднее | Сохранить буферные недели (недели 10-12) для доработок; приоритизировать ключевые задачи O1-O3 |

10. Резюме

В данном предложении представлено исследование, направленное на четко выявленный пробел в существующей литературе по обнаружению эксфильтрации данных. Современные системы обнаружения - сетевые, хостовые, predictive или hybrid - остаются фундаментально ограниченными из-за зависимости от одномодальной телеметрии и неспособности моделировать последовательные поведенческие паттерны, характерные для многоэтапных атак эксфильтрации.

В ответ на это предложение вводит поведенчески ориентированную гибридную архитектуру машинного обучения, объединяющую три ключевых компонента: слой многoисточниковой интеграции данных, объединяющий хостовую и сетевую телеметрию; гибридный слой классификации ML/DL, использующий ансамблевые методы и архитектуры глубокого обучения; и слой моделирования поведенческих последовательностей на основе LSTM-сети. на основе SHAP объяснимость будет дополнительно включена для повышения интерпретируемости решений обнаружения.

Исследование направляется четырьмя исследовательскими вопросами, связанными с выявлением междоменных признаков, проектированием гибридной архитектуры, моделированием поведенческих последовательностей и интеграцией объяснимости. Эти вопросы сопоставлены с четырьмя задачами, каждая из которых представляет конкретную и оцениваемую единицу работы. Использование публично доступных эталонные наборы данных ограничивает область исследования и обеспечивает этическое соответствие и воспроизводимость. 12-недельный план исследования структурирован в пять методологических фаз с определенными вехами и стратегиями снижения рисков.

Значимость этого исследования имеет как академическое, так и практическое измерение. Оно будет развивать существующие гибридные архитектуры обнаружения за счет улучшения моделирования поведенческих последовательностей и многoисточниковой интеграции признаков, а также предоставит воспроизводимые результаты исследовательскому сообществу. На практике оно улучшит раннее обнаружение скрытных многоэтапных атак и повысит интерпретируемость моделей для команд security operations.

В заключение, предлагаемая архитектура представляет своевременный и обоснованный вклад в кибербезопасность, напрямую устраняя ограничения существующих подходов и отвечая на новые исследовательские приоритеты в области интеграции многoисточниковой телеметрии, поведенческого моделирования и объяснимого обнаружения вторжений.

Список литературы

Açıkgözoğlu, E. (2024). Сравнение алгоритмов машинного обучения для обнаружения эксфильтрации данных через DNS. Yalvaç Akademi Dergisi, 9(2), 61-70. https://doi.org/10.57120/yalvac.1507402

Almuhanna, R., & Dardouri, S. (2025). Подход глубокого и машинного обучения для anomaly-based обнаружения сетевых вторжений. Frontiers in Artificial Intelligence, 8, 1625891. https://doi.org/10.3389/frai.2025.1625891

Balogun, S. A., Ijiga, O. M., Okika, N., Enyejo, L. A., & Agbo, O. J. (2025). Обнаружение SQL injection и эксфильтрации данных на основе машинного обучения через поведенческое профилирование relational query patterns. International Journal of Innovative Science and Research Technology, 49-63. https://doi.org/10.38124/ijisrt/25aug324

Cai, X., Zhang, H., Ahmed, C. M., & Koide, H. (2025). Обнаружение эксфильтрации продвинутых устойчивых угроз с помощью ensemble глубокого обучения tree models и новых метрик обнаружения. IEEE Access, 13, 81803-81822. https://doi.org/10.1109/access.2025.3567772

Chen, Z., Simsek, M., Kantarci, B., Bagheri, M., & Djukic, P. (2024). Гибридная система обнаружения вторжений с поддержкой машинного обучения, преобразованием хостовых данных и advanced two-stage classifier. Computer Networks, 250, 110576. https://doi.org/10.1016/j.comnet.2024.110576

Chinnasamy, R., Subramanian, M., Easwaramoorthy, S. V., & Cho, J. (2025). Методы сетевые IDS на основе глубокого обучения: систематический обзор. ICT Express, 11(1), 181-215. https://doi.org/10.1016/j.icte.2025.01.005

Hakim, A. R., Ramli, K., Salman, M., Pranggono, B., & Agustina, E. R. (2024). ARKAIV: прогнозирование эксфильтрации данных с использованием обучения с учителем machine learning на основе tactic mapping из threat reports и event logs. IEEE Access, 13, 28381-28397. https://doi.org/10.1109/access.2024.3524502

Hanintya, D. L., Sukarno, P., & Wardana, A. A. (2025). Сравнение XAI-фреймворков: кейс обнаружения DNS exfiltration attack с использованием neural network. Procedia Computer Science, 269, 1022-1032. https://doi.org/10.1016/j.procs.2025.09.044

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science в исследованиях информационных систем. MIS Quarterly, 28(1), 75-105. https://doi.org/10.2307/25148625

Hozouri, A., Mirzaei, A., & Effatparvar, M. (2025). Комплексный обзор систем обнаружения вторжений с учетом достижений машинного обучения, глубокого обучения и новых вызовов кибербезопасности. Discover Artificial Intelligence, 5(1). https://doi.org/10.1007/s44163-025-00578-1

Kamal, H., & Mashaly, M. (2025). Устойчивая система обнаружения вторжений с использованием улучшенной гибридной модели глубокого обучения для binary и multi-class classification в IoT-сетях. Technologies, 13(3), 102. https://doi.org/10.3390/technologies13030102

Kuppuraju, S. Y., Ojha, S. S., & Kumar, M. (2025). Обнаружение эксфильтрации данных в реальном времени с использованием глубокого обучения в edge computing systems. International Journal of Innovative Research in Computer Science & Technology, 13(2), 6-13. https://doi.org/10.55524/ijircst.2025.13.2.2

Ofori, H. K., Bell-Dzide, K., Brown-Acquaye, W. L., Lempogo, F., Frimpong, S. O., Agbehadji, I. E., & Millham, R. C. (2025). Применение методов машинного и глубокого обучения для улучшенного обнаружения инсайдерских угроз в кибербезопасности: библиометрический обзор. Symmetry, 17(10), 1704. https://doi.org/10.3390/sym17101704

Potluri, S. (2024). Фреймворк на основе глубокого обучения для обнаружения аномальных утечек данных в распределенных cloud storage infrastructures. International Journal of Artificial Intelligence Data Science and Machine Learning, 5(3). https://doi.org/10.63282/3050-9262.ijaidsml-v5i3p109

Qutqut, M. H., Ahmed, A., Taqi, M. K., Abimanyu, J., Ajes, E. T., & Alhaj, F. (2026). Сравнительная оценка Snort и Suricata для обнаружения туннелей эксфильтрации данных в облачных средах. Journal of Cybersecurity and Privacy, 6(1), 17. https://doi.org/10.3390/jcp6010017

Sammour, M., Othman, M. F. I., Hassan, A., Bhais, O., & Talib, M. S. (2026). Продвинутое обнаружение DNS-туннелирование: гибридный подход reinforcement learning и metaheuristic. Frontiers in Computer Science, 7. https://doi.org/10.3389/fcomp.2025.1728980

Singh, P. R. N., & Siddalingaiah, N. (2025). Профилирование риска на уровне разрешений и обнаружение аномалий в IoT с использованием машинного обучения. International Journal of Information Technology. https://doi.org/10.1007/s41870-025-02977-0

Thomas, R., Yerima, S. Y., Alkharoossi, S. K., Alkhoori, M. M., & Ahmed, A. (2025). DNS exfiltration attack и генерация набора данных для machine learning-based detection. 3rd International Conference on Cyber Resilience ICCR2025, 1-6. https://doi.org/10.1109/iccr67387.2025.11292120

Yumlembam, R., Issac, B., Jacob, S. M., Yang, L., & Krishnan, D. (2025). Обнаружение инсайдерских угроз с использованием GCN и Bi-LSTM с явными и неявными graph representations. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2512.18483

Zuppelli, M., Guarascio, M., Caviglione, L., & Liguori, A. (2024). Нет места для leaking containers: обнаружение эксфильтрации секретов с помощью AI и системных вызовов. ARES '24: Proceedings of the 19th International Conference on Availability, Reliability and Security (July 2024), 1-8. https://doi.org/10.1145/3664476.3670884
