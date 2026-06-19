# Code Architecture

This directory is the entry point for the current project architecture. It documents the implemented code, not planned functionality.

## System Overview

```text
manage.py
  -> scripts/router_script.py
    -> scripts/handlers/*          Stage One dataset analysis/sorting
    -> scripts/stage_two/cli.py     Stage Two catalog/parser/normalization checks
```

Stage One produces analysis and sorted-path JSON artifacts and prepares the filtered dataset tree. Stage Two uses `PATH_FOLDER_DATASETS_FILTER` and PostgreSQL catalog rows to normalize files into Parquet and register traceability. `PATH_FOLDER_DATASETS` remains the immutable raw source root for Stage One and audit/backtracking.

## Documents

- [General architecture](general-architecture.md): repository layout, modules, and data flow.
- [Router architecture](router-architecture.md): `manage.py`, module/service/action routing, and CLI argument behavior.
- [Stage One architecture](stage-one-architecture.md): handler pipeline, sorted JSON outputs, and Stage One boundaries.
- [Stage Two architecture](stage-two-architecture.md): catalog, parser registry, normalization, reports, and checks.
- [DB architecture](db-architecture.md): SQLAlchemy, Alembic, repositories, and catalog tables.
- [Pipeline artifacts and contracts](pipeline-artifacts-and-contracts.md): JSON, schema, Parquet, report, and catalog artifacts.
- [Extension points and risks](extension-points-and-risks.md): safe ways to extend parsers and known technical debt.

Handler-specific legacy documents are still available:

- `hadlers_analyze_dataset_architecture.md`
- `hadlers_sort_architecture.md`
- `hadlers_save_sort_architecture.md`
- `hadlers_filter_dataset_architecture.md`
- `hadlers_dns_analyze_architecture.md`
- `hadlers_host_analyze_architecture.md`
- `hadlers_json_handler_architecture.md`

The filename typo `hadlers_*` is preserved to avoid breaking existing links.

## Main Runtime Paths

| Path | Purpose |
| --- | --- |
| `config.py` | Central project configuration and path construction. |
| `manage.py` | CLI entrypoint. |
| `scripts/router_script.py` | Top-level router for `handlers` and `stage-two`. |
| `scripts/handlers/` | Stage One analysis, sorting, filtering, and JSON utilities. |
| `scripts/db/` | SQLAlchemy session, models, repositories, Alembic migration, DB smoke checks. |
| `scripts/stage_two/` | Stage Two storage, ingestion, parser registry, parsers, normalization, quality, traceability. |
| `schemas/` | JSON schema contracts for normalized, feature, and model-ready artifacts. |
| `tests/stage_two/` | Unit and smoke tests for Stage Two. |
| `docs/en/normalization/` | Operational Stage Two documentation. |

## Current Boundaries

- Stage One is filesystem/JSON oriented.
- Stage Two is PostgreSQL catalog plus Parquet artifact oriented.
- Raw datasets are read-only inputs and are not the default Stage Two catalog source.
- Stage Two processing roles are limited to TRAIN, VALIDATION, and TEST.
- Full parser normalization is implemented.
- Feature/model-ready contracts exist, but full production feature/model-ready CLI is not implemented in the current parser workflow.
