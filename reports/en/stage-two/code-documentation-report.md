# Code Documentation Report

Execution date: 2026-06-22.

English code documentation was created at:

```text
docs/en/code-documentation/
```

Report path:

```text
reports/en/stage-two/code-documentation-report.md
```

## Created Documents

| Document | Purpose |
|---|---|
| `README.md` | index, document map, invariants, key commands |
| `cli_and_routing.md` | `manage.py`, handler routes, Stage Two CLI routes and arguments |
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

## Coverage

Covered:

- repository structure overview;
- CLI and routing layer;
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

## Commands Documented

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

## Components Covered

| Component | Files |
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

## Known Limitations

- English documentation is a technical translation/adaptation of the Russian `docs/ru/code-documentation` section.
- Feature/model-ready services exist, but a full end-to-end CLI for feature extraction/model-ready assembly is not implemented yet.
- Stage One statuses can lag parser implementation; current runnable coverage should be checked with `stage-two parser-coverage`.
- Host filter whitelist is hardcoded in Python.
- Host role fallback in `HostDatasetHandler` is `TEST`, which requires caution for new source paths.
- Some formats are semantically ambiguous, for example `wls_day` in analysis docs vs current `HostNetflowParser` registry mapping.

## Follow-up Tasks

1. Keep RU and EN documentation synchronized after parser or CLI changes.
2. Move Host filter whitelist to versioned config with tests.
3. Add dedicated WLS parser or clarify `wls_day` registry mapping.
4. Implement CLI for feature extraction and model-ready build with mandatory leakage gate.
5. Register feature/model-ready schema versions like normalized schema.
6. Add CI checks for Markdown links, parser seed validation, leakage contracts, and ORM/migration consistency.
