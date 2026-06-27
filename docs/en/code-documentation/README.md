# Project Code Documentation

This section documents the `Proposal` codebase for a developer who needs to understand the DNS/Host dataset preparation and normalization pipeline without reading every source file first.

The documentation covers Stage One filesystem analysis, Stage Two catalog-backed normalization, PostgreSQL metadata, SQLAlchemy repositories, parser strategy, label handling, Parquet/DuckDB artifacts, quality and leakage checks, storage layout, dataset contracts, risks, and extension points.

## Document Map

| Document | Purpose |
|---|---|
| [cli_and_routing.md](cli_and_routing.md) | `manage.py`, routing layer, Stage One/Stage Two commands, execution order |
| [stage_one_handlers.md](stage_one_handlers.md) | Stage One handlers: dataset analysis, filtering, sorting, path export, content analysis, JSON management |
| [stage_two_overview.md](stage_two_overview.md) | End-to-end Stage Two pipeline: storage, ingestion, registry, normalization, checks |
| [storage_architecture.md](storage_architecture.md) | `PATH_DATA_STORAGE`, required directories, artifact paths |
| [postgresql_catalog.md](postgresql_catalog.md) | PostgreSQL catalog tables and traceability chain |
| [sqlalchemy_layer.md](sqlalchemy_layer.md) | config, session handling, models, repositories, migrations, smoke check |
| [normalized_event_schema.md](normalized_event_schema.md) | `normalized_event_v1`, fields, timestamp, labels, traceability |
| [parser_strategy.md](parser_strategy.md) | parser registry, resolver, parser classes, parser statuses |
| [label_resolver.md](label_resolver.md) | label sources, TEST restrictions, conflicts |
| [parquet_and_duckdb.md](parquet_and_duckdb.md) | Parquet writer, paths, compression, DuckDB views/checks |
| [data_quality_checks.md](data_quality_checks.md) | DataQualityChecker, DuckDB analytics, reports |
| [data_leakage_prevention.md](data_leakage_prevention.md) | forbidden X columns, TRAIN/VALIDATION/TEST invariants |
| [traceability.md](traceability.md) | lineage from raw file to model-ready artifact |
| [dataset_contracts.md](dataset_contracts.md) | DNS/Host TRAIN/VALIDATION/TEST formats, counts, labels, parser needs |
| [extension_points.md](extension_points.md) | how to add handlers, parsers, schemas, labels, checks, stages |
| [risks_and_technical_debt.md](risks_and_technical_debt.md) | known limitations, parser gaps, leakage/timestamp/large-file risks |

## Recommended Reading Order

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

Stage One inspects DNS/Host dataset directories, creates JSON inventories, filters Host sources, sorts files by role and format, exports path maps for the sorted tree, and generates content analysis reports.

Implemented components live under:

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

Stage One does not register files in PostgreSQL and does not write normalized/features/model-ready artifacts. Its outputs are filesystem and JSON inputs for later catalog ingestion and parser planning.

## Stage Two

Stage Two creates the storage structure, registers raw/sorted files in PostgreSQL Catalog, seeds schema and parser metadata, resolves parsers, normalizes events into Parquet, writes parser reports, runs DuckDB/quality/leakage checks, and preserves lineage from raw files to model-ready artifacts.

Implemented components live under `scripts/stage_two`, `scripts/db`, and `schemas`.

## Core Invariants

1. Raw dataset files are not modified.
2. `TRAIN`, `VALIDATION`, and `TEST` are not mixed in one model-ready artifact.
3. `TEST` is not used for training, preprocessing fit, scaler fit, encoder fit, threshold tuning, or feature selection.
4. PostgreSQL stores metadata, statuses, links, paths, hashes, and reports; it does not store large normalized/features/model-ready tables.
5. Parquet is used for normalized events, feature artifacts, and model-ready artifacts.
6. DuckDB is used for analytical SQL checks over Parquet.
7. Labels are stored separately from X features.
8. Leakage/source/label fields are not allowed in model-ready X artifacts.
9. All artifacts must preserve traceability.
10. Missing labels must not be treated as benign.
11. TEST filename heuristics for label inference are disabled in `LabelResolver`.
12. Missing timestamps must not be synthetically replaced with current time.

## Main CLI Commands

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

Detailed arguments and ordering are documented in [cli_and_routing.md](cli_and_routing.md).
