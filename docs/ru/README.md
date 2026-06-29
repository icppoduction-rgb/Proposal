# Документация проекта Proposal

Этот README является общей точкой входа в документацию проекта. Он помогает быстро найти материалы по исследовательскому контексту, Stage One, Stage Two normalization, архитектуре кода, датасетам, PostgreSQL Catalog, Parquet/DuckDB, labels, features и leakage checks.

Документация разделяет:

- **фактическую реализацию** - то, что подтверждено текущим кодом и CLI;
- **операционные инструкции** - как запускать и проверять pipeline;
- **исследовательские материалы и proposal** - цели, методология, dataset strategy, feature catalogue и планы;
- **gaps и follow-up** - то, что еще не реализовано или требует уточнения.

## Быстрый старт

| Если нужно | Читать |
| --- | --- |
| Понять весь проект и исследовательский контекст | [project_overview_and_research_context.md](project_overview_and_research_context.md) |
| Увидеть карту ключевых документов | [project_documentation_index.md](project_documentation_index.md) |
| Проверить, что реализовано, а что пока proposal | [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) |
| Разобраться в структуре кода и CLI | [code-documentation/README.md](code-documentation/README.md) |
| Найти Stage One анализ датасетов | [analysis-dataset/README.md](analysis-dataset/README.md) |
| Запустить Stage Two normalization | [normalization/README.md](normalization/README.md), [normalization/stage_two_commands.md](normalization/stage_two_commands.md) |
| Выбрать DNS/Host стратегию и split roles | [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md) |
| Смотреть feature engineering и leakage exclusions | [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) |

## Основные разделы

| Раздел | Назначение | Тип |
| --- | --- | --- |
| [analysis-dataset/](analysis-dataset/README.md) | Результаты Stage One анализа DNS/Host buckets, counts, formats, labels, readiness и parser recommendations. | Фактический анализ датасетов |
| [code-documentation/](code-documentation/README.md) | Архитектура кода: CLI/routing, Stage One handlers, Stage Two, PostgreSQL Catalog, SQLAlchemy, schemas, parsers, labels, Parquet/DuckDB, checks, risks. | Техническая документация по коду |
| [normalization/](normalization/README.md) | Operational guide по Stage Two normalization: storage, catalog ingestion, parser registry, `READY_FOR_PARSING`, normalization commands, DuckDB/leakage checks, traceability. | Фактическая реализация и runbooks |
| [project_documentation_index.md](project_documentation_index.md) | Индекс верхнеуровневых документов и карта переноса старых материалов. | Навигация |
| [project_overview_and_research_context.md](project_overview_and_research_context.md) | Research context, цели, methodology, proposal-level architecture и ограничения. | Research/proposal |
| [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md) | DNS/Host dataset strategy с явным разделением `TRAIN`, `VALIDATION`, `TEST`. | Dataset strategy |
| [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) | Feature extraction map, feature groups, schema requirements, forbidden leakage fields, implementation priorities. | Feature engineering |
| [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) | Подтвержденная реализация, proposal-level gaps, QA и follow-up tasks. | QA/gaps |
| [Project Proposal.docx](<Project Proposal.docx>) | Русская версия проектного proposal-документа в DOCX. | Research/proposal artifact |

## Где искать по темам

### Stage One

- [code-documentation/stage_one_handlers.md](code-documentation/stage_one_handlers.md) - handlers `analyze_dataset`, `filter_dataset`, `sort`, `save_sort`, `dns_analyze`, `host_analyze`, JSON manager.
- [analysis-dataset/README.md](analysis-dataset/README.md) - итоговый индекс анализа датасетов.
- [analysis-dataset/dns_datasets.md](analysis-dataset/dns_datasets.md) - DNS `TRAIN` / `VALIDATION` / `TEST`.
- [analysis-dataset/host_datasets.md](analysis-dataset/host_datasets.md) - Host `TRAIN` / `VALIDATION` / `TEST`.
- [analysis-dataset/format_status_matrix.md](analysis-dataset/format_status_matrix.md) - readiness matrix по 66 format buckets.
- [analysis-dataset/labels_and_readiness.md](analysis-dataset/labels_and_readiness.md) - labels, readiness statuses и anti-leakage правила.

### Stage Two / Normalization

- [normalization/README.md](normalization/README.md) - границы Stage Two, основные команды, инварианты.
- [normalization/stage_two_commands.md](normalization/stage_two_commands.md) - полный reference по Stage Two commands: входы, выходы, PostgreSQL statuses, ошибки и проверки.
- [normalization/usage_guide.md](normalization/usage_guide.md) - общий порядок запуска CLI.
- [normalization/runtime_resource_runbook.md](normalization/runtime_resource_runbook.md) - эксплуатация, recovery и large-file сценарии.
- [normalization/performance_tuning.md](normalization/performance_tuning.md) - `workers`, `batch-size`, `max-output-part-rows`, packet modes.

### Архитектура кода

- [code-documentation/README.md](code-documentation/README.md) - карта технической документации.
- [code-documentation/cli_and_routing.md](code-documentation/cli_and_routing.md) - `manage.py`, routing layer, Stage One/Stage Two commands.
- [code-documentation/stage_two_overview.md](code-documentation/stage_two_overview.md) - Stage Two pipeline.
- [code-documentation/extension_points.md](code-documentation/extension_points.md) - как расширять handlers, parsers, schemas, labels, checks и stages.
- [code-documentation/risks_and_technical_debt.md](code-documentation/risks_and_technical_debt.md) - known limitations, parser gaps, leakage/timestamp/large-file risks.

### PostgreSQL Catalog и SQLAlchemy

- [code-documentation/postgresql_catalog.md](code-documentation/postgresql_catalog.md) - catalog tables и traceability chain.
- [code-documentation/sqlalchemy_layer.md](code-documentation/sqlalchemy_layer.md) - config, session, models, repositories, migrations.
- [normalization/postgresql_catalog_schema.md](normalization/postgresql_catalog_schema.md) - Stage Two catalog schema с точки зрения normalization.

### Schemas, Parsers и Labels

- [code-documentation/normalized_event_schema.md](code-documentation/normalized_event_schema.md) - normalized event schema.
- [normalization/normalized_event_schema.md](normalization/normalized_event_schema.md) - operational schema guide для normalization.
- [code-documentation/parser_strategy.md](code-documentation/parser_strategy.md) и [normalization/parser_strategy.md](normalization/parser_strategy.md) - parser registry/resolver strategy.
- [normalization/parser_development_guide.md](normalization/parser_development_guide.md) - добавление нового parser implementation.
- [code-documentation/label_resolver.md](code-documentation/label_resolver.md) и [normalization/label_resolver.md](normalization/label_resolver.md) - label sources, `TEST` restrictions, conflicts.

### Parquet, DuckDB, Quality и Leakage

- [code-documentation/parquet_and_duckdb.md](code-documentation/parquet_and_duckdb.md) - Parquet paths, writer, DuckDB views/checks.
- [normalization/parquet_duckdb_artifacts.md](normalization/parquet_duckdb_artifacts.md) - artifacts и DuckDB usage в Stage Two.
- [normalization/data_quality_checks.md](normalization/data_quality_checks.md) - DataQuality/DuckDB checks.
- [normalization/data_leakage_prevention.md](normalization/data_leakage_prevention.md) - forbidden X columns и anti-leakage invariants.
- [code-documentation/traceability.md](code-documentation/traceability.md) и [normalization/traceability.md](normalization/traceability.md) - `raw -> normalized -> features -> model-ready`.

### Features и исследовательские материалы

- [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) - feature groups, contracts, exclusions и priorities.
- [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md) - dataset roles, sources, strategy и limitations.
- [project_overview_and_research_context.md](project_overview_and_research_context.md) - research framing и proposal-level архитектура.
- [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) - где proposal расходится с текущей реализацией.

## Рекомендуемый порядок чтения

1. [project_documentation_index.md](project_documentation_index.md) - общий индекс и карта объединенных документов.
2. [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) - граница между реализованным и proposal.
3. [analysis-dataset/README.md](analysis-dataset/README.md) - фактическая структура DNS/Host данных.
4. [code-documentation/README.md](code-documentation/README.md) - архитектура кода и pipeline.
5. [normalization/README.md](normalization/README.md) - Stage Two implementation guide.
6. [normalization/stage_two_commands.md](normalization/stage_two_commands.md) - точные команды запуска.
7. [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) - feature engineering и model-ready ограничения.

## Основные инварианты

1. Raw-файлы не изменяются.
2. `TRAIN`, `VALIDATION` и `TEST` не смешиваются.
3. `TEST` не используется для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
4. PostgreSQL хранит metadata, статусы, связи, пути, хеши и отчеты; большие normalized/features/model-ready таблицы хранятся в Parquet.
5. Labels не являются input features.
6. Leakage/source/label fields не попадают в model-ready X artifacts.
7. Отсутствующий label не означает benign.
8. Отсутствующий timestamp нельзя заменять текущим временем.
9. Traceability должна сохраняться по цепочке `raw -> normalized -> features -> model-ready`.
## Stage Two performance quick start

Для текущей performance architecture используйте:

- [normalization/performance_tuning.md](normalization/performance_tuning.md) - resource profiles, format policy, benchmark target и troubleshooting.
- [normalization/runtime_resource_runbook.md](normalization/runtime_resource_runbook.md) - operational sequence для benchmark/full runs и recovery.
- [normalization/stage_two_commands.md](normalization/stage_two_commands.md) - точный CLI reference, включая `benchmark-normalization`.
- [code-documentation/stage_two_overview.md](code-documentation/stage_two_overview.md) - execution planner, bounded multiprocessing, chunking, atomic Parquet, benchmark и validation architecture.

Рекомендуемый flow:

```bash
python manage.py stage-two benchmark-normalization --branch host --role TEST --format txt --limit 10000 --sample-ratio 0.10 --resource-profile fast
python manage.py stage-two normalize-format --branch host --role TEST --format txt --resource-profile fast --resume
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Начинайте с `safe` или `balanced`; используйте `fast` или `aggressive` только после чистых benchmark reports и quality gates.
