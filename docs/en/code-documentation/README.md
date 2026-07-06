# Project Code Documentation

This section documents the `Proposal` codebase for a developer who needs to understand the DNS/Host dataset preparation, normalization, and Stage Three feature/model-ready pipeline without reading every source file first.

The documentation covers Stage One filesystem analysis, Stage Two catalog-backed normalization, Stage Three feature/model-ready preparation, PostgreSQL metadata, SQLAlchemy repositories, parser strategy, label handling, Parquet/DuckDB artifacts, quality and leakage checks, storage layout, dataset contracts, risks, and extension points.

## Document Map

| Document | Purpose |
|---|---|
| [cli_and_routing.md](cli_and_routing.md) | `manage.py`, routing layer, Stage One/Stage Two commands, execution order |
| [stage_one_handlers.md](stage_one_handlers.md) | Stage One handlers: dataset analysis, filtering, sorting, path export, content analysis, JSON management |
| [stage_two_overview.md](stage_two_overview.md) | End-to-end Stage Two pipeline: storage, ingestion, registry, normalization, checks |
| [stage_three_overview.md](stage_three_overview.md) | Stage Three pipeline: feature catalog, extraction, preprocessing, model-ready build, checks, final report |
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
4. [stage_three_overview.md](stage_three_overview.md)
5. [postgresql_catalog.md](postgresql_catalog.md)
6. [normalized_event_schema.md](normalized_event_schema.md)
7. [parser_strategy.md](parser_strategy.md)
8. [label_resolver.md](label_resolver.md)
9. [data_leakage_prevention.md](data_leakage_prevention.md)
10. [dataset_contracts.md](dataset_contracts.md)
11. [risks_and_technical_debt.md](risks_and_technical_debt.md)

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

Current code sync, checked on 2026-07-04:

- `router_stage_two()` supports `bootstrap-storage`, `catalog-ingest`, `seed-parser-registry`, `parser-coverage`, `mark-ready`, `normalize-format`, `normalize-all`, `benchmark-normalization`, `split-large-files`, `normalize-dns`, `normalize-host`, `run-duckdb-checks`, `run-leakage-checks`, and `trace-artifact`.
- `config.manage_commands` is only a fallback printed command list and is not complete for newer Stage Two commands.
- `normalize-format` and `benchmark-normalization` resolve resource profiles and format-specific runtime policy before execution; `normalize-all` resolves shared runtime options but does not apply per-format policy in the CLI route.
- Stage Three feature/model-ready preparation lives under `scripts/stage_three` and is exposed through `python manage.py stage-three ...`. The training/evaluation pipeline belongs to Stage Four and is not exposed yet.

## Stage Three

Stage Three reads catalog-backed normalized artifacts, validates the feature catalog, extracts features, separates X/y/metadata/traceability, applies preprocessing utilities, builds model-ready artifacts, runs checks, and writes the final report.

Implemented components live under `scripts/stage_three`.

Details: [stage_three_overview.md](stage_three_overview.md).

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

python manage.py stage-three validate-inputs --branch dns --role TRAIN
python manage.py stage-three build-feature-catalog
python manage.py stage-three probe-runtime-backend --backend auto
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
python manage.py stage-three final-report --experiment-id exp001
```

Detailed arguments and ordering are documented in [cli_and_routing.md](cli_and_routing.md).
