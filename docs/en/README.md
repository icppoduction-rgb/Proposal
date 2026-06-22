# Proposal Project Documentation

This README is the main entry point for the project documentation. It helps locate materials for the research context, Stage One, Stage Two normalization, code architecture, datasets, PostgreSQL Catalog, Parquet/DuckDB, labels, features, and leakage checks.

The documentation separates:

- **implemented behavior** - confirmed by current code and CLI;
- **operational instructions** - how to run and verify the pipeline;
- **research and proposal materials** - objectives, methodology, dataset strategy, feature catalogue, and plans;
- **gaps and follow-up** - work that is not implemented yet or needs clarification.

## Quick Start

| Need | Read |
| --- | --- |
| Understand the project and research context | [project_overview_and_research_context.md](project_overview_and_research_context.md) |
| See the key documentation map | [project_documentation_index.md](project_documentation_index.md) |
| Check what is implemented and what is proposal-level | [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) |
| Understand code structure and CLI | [code-documentation/README.md](code-documentation/README.md) |
| Find Stage One dataset analysis | [analysis-dataset/README.md](analysis-dataset/README.md) |
| Run Stage Two normalization | [normalization/README.md](normalization/README.md), [normalization/stage_two_commands.md](normalization/stage_two_commands.md) |
| Choose DNS/Host strategy and split roles | [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md) |
| Review feature engineering and leakage exclusions | [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) |

## Main Sections

| Section | Purpose | Type |
| --- | --- | --- |
| [analysis-dataset/](analysis-dataset/README.md) | Stage One DNS/Host bucket analysis, counts, formats, labels, readiness, and parser recommendations. | Factual dataset analysis |
| [code-documentation/](code-documentation/README.md) | Code architecture: CLI/routing, Stage One handlers, Stage Two, PostgreSQL Catalog, SQLAlchemy, schemas, parsers, labels, Parquet/DuckDB, checks, risks. | Technical code documentation |
| [normalization/](normalization/README.md) | Operational guide for Stage Two normalization: storage, catalog ingestion, parser registry, `READY_FOR_PARSING`, normalization commands, DuckDB/leakage checks, traceability. | Implemented behavior and runbooks |
| [project_documentation_index.md](project_documentation_index.md) | Index of top-level documents and map of merged legacy materials. | Navigation |
| [project_overview_and_research_context.md](project_overview_and_research_context.md) | Research context, objectives, methodology, proposal-level architecture, and limitations. | Research/proposal |
| [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md) | DNS/Host dataset strategy with explicit `TRAIN`, `VALIDATION`, and `TEST` separation. | Dataset strategy |
| [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) | Feature extraction map, feature groups, schema requirements, forbidden leakage fields, implementation priorities. | Feature engineering |
| [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) | Confirmed implementation, proposal-level gaps, QA, and follow-up tasks. | QA/gaps |
| [Project Proposal.docx](<Project Proposal.docx>) | English project proposal artifact in DOCX format. | Research/proposal artifact |

## Where to Look by Topic

### Stage One

- [code-documentation/stage_one_handlers.md](code-documentation/stage_one_handlers.md) - handlers `analyze_dataset`, `filter_dataset`, `sort`, `save_sort`, `dns_analyze`, `host_analyze`, JSON manager.
- [analysis-dataset/README.md](analysis-dataset/README.md) - dataset analysis index.
- [analysis-dataset/dns_datasets.md](analysis-dataset/dns_datasets.md) - DNS `TRAIN` / `VALIDATION` / `TEST`.
- [analysis-dataset/host_datasets.md](analysis-dataset/host_datasets.md) - Host `TRAIN` / `VALIDATION` / `TEST`.
- [analysis-dataset/format_status_matrix.md](analysis-dataset/format_status_matrix.md) - readiness matrix for 66 format buckets.
- [analysis-dataset/labels_and_readiness.md](analysis-dataset/labels_and_readiness.md) - labels, readiness statuses, and anti-leakage rules.

### Stage Two / Normalization

- [normalization/README.md](normalization/README.md) - Stage Two scope, main commands, and invariants.
- [normalization/stage_two_commands.md](normalization/stage_two_commands.md) - full Stage Two command reference: inputs, outputs, PostgreSQL statuses, errors, and verification.
- [normalization/usage_guide.md](normalization/usage_guide.md) - general CLI run order.
- [normalization/runtime_resource_runbook.md](normalization/runtime_resource_runbook.md) - operations, recovery, and large-file scenarios.
- [normalization/performance_tuning.md](normalization/performance_tuning.md) - `workers`, `batch-size`, `max-output-part-rows`, packet modes.

### Code Architecture

- [code-documentation/README.md](code-documentation/README.md) - technical documentation map.
- [code-documentation/cli_and_routing.md](code-documentation/cli_and_routing.md) - `manage.py`, routing layer, Stage One/Stage Two commands.
- [code-documentation/stage_two_overview.md](code-documentation/stage_two_overview.md) - Stage Two pipeline.
- [code-documentation/extension_points.md](code-documentation/extension_points.md) - how to extend handlers, parsers, schemas, labels, checks, and stages.
- [code-documentation/risks_and_technical_debt.md](code-documentation/risks_and_technical_debt.md) - known limitations, parser gaps, leakage/timestamp/large-file risks.

### PostgreSQL Catalog and SQLAlchemy

- [code-documentation/postgresql_catalog.md](code-documentation/postgresql_catalog.md) - catalog tables and traceability chain.
- [code-documentation/sqlalchemy_layer.md](code-documentation/sqlalchemy_layer.md) - config, sessions, models, repositories, migrations.
- [normalization/postgresql_catalog_schema.md](normalization/postgresql_catalog_schema.md) - Stage Two catalog schema from the normalization perspective.

### Schemas, Parsers, and Labels

- [code-documentation/normalized_event_schema.md](code-documentation/normalized_event_schema.md) - normalized event schema.
- [normalization/normalized_event_schema.md](normalization/normalized_event_schema.md) - operational schema guide for normalization.
- [code-documentation/parser_strategy.md](code-documentation/parser_strategy.md) and [normalization/parser_strategy.md](normalization/parser_strategy.md) - parser registry/resolver strategy.
- [normalization/parser_development_guide.md](normalization/parser_development_guide.md) - adding a new parser implementation.
- [code-documentation/label_resolver.md](code-documentation/label_resolver.md) and [normalization/label_resolver.md](normalization/label_resolver.md) - label sources, `TEST` restrictions, conflicts.

### Parquet, DuckDB, Quality, and Leakage

- [code-documentation/parquet_and_duckdb.md](code-documentation/parquet_and_duckdb.md) - Parquet paths, writer, DuckDB views/checks.
- [normalization/parquet_duckdb_artifacts.md](normalization/parquet_duckdb_artifacts.md) - artifacts and DuckDB usage in Stage Two.
- [normalization/data_quality_checks.md](normalization/data_quality_checks.md) - DataQuality/DuckDB checks.
- [normalization/data_leakage_prevention.md](normalization/data_leakage_prevention.md) - forbidden X columns and anti-leakage invariants.
- [code-documentation/traceability.md](code-documentation/traceability.md) and [normalization/traceability.md](normalization/traceability.md) - `raw -> normalized -> features -> model-ready`.

### Features and Research Materials

- [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) - feature groups, contracts, exclusions, and priorities.
- [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md) - dataset roles, sources, strategy, and limitations.
- [project_overview_and_research_context.md](project_overview_and_research_context.md) - research framing and proposal-level architecture.
- [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) - where the proposal differs from the current implementation.

## Recommended Reading Order

1. [project_documentation_index.md](project_documentation_index.md) - global index and merged-document map.
2. [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) - boundary between implemented behavior and proposal.
3. [analysis-dataset/README.md](analysis-dataset/README.md) - factual DNS/Host data structure.
4. [code-documentation/README.md](code-documentation/README.md) - code architecture and pipeline.
5. [normalization/README.md](normalization/README.md) - Stage Two implementation guide.
6. [normalization/stage_two_commands.md](normalization/stage_two_commands.md) - exact run commands.
7. [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) - feature engineering and model-ready constraints.

## Core Invariants

1. Raw files are not modified.
2. `TRAIN`, `VALIDATION`, and `TEST` are not mixed.
3. `TEST` is not used for training, preprocessing fit, scaler/encoder fit, feature selection, or threshold tuning.
4. PostgreSQL stores metadata, statuses, relationships, paths, hashes, and reports; large normalized/features/model-ready tables are stored in Parquet.
5. Labels are not input features.
6. Leakage/source/label fields are not included in model-ready X artifacts.
7. A missing label does not mean benign.
8. Missing timestamps must not be replaced with current time.
9. Traceability must be preserved through `raw -> normalized -> features -> model-ready`.
