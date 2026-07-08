# Repository Analysis

Review date: 2026-07-08.

This document records the current state of the `Proposal` repository after reviewing entrypoints, CLI routing, Stage One/Two/Three modules, tests, schemas, and storage artifacts.

## Executive Summary

The repository implements the data-preparation pipeline up to model-ready artifacts:

```text
Stage One:   raw datasets -> inventories/sorted path maps/content reports
Stage Two:   raw catalog -> parser registry -> normalized Parquet -> quality/leakage/traceability
Stage Three: normalized Parquet -> feature artifacts -> model-ready X/y/metadata/traceability -> readiness report
Stage Four:  training/evaluation/explainability, not exposed as CLI yet
```

Stage Four remains future work: RF/XGBoost/CNN/LSTM training, threshold tuning, SHAP/XAI, and experimental evaluation are not implemented in the current CLI.

## Code and Documentation Size

Current snapshot:

| Area | Count |
| --- | ---: |
| Python files | 334 |
| Test Python files | 66 |
| Markdown files in `docs/` | 106 |
| Markdown files in `docs/ru` | 52 before adding this file |
| Markdown files in `docs/en` | 52 before adding this file |

Main directories:

```text
scripts/
  handlers/        # Stage One handlers
  stage_two/       # catalog, parsers, normalization, checks
  stage_three/     # feature/model-ready preparation
  db/              # SQLAlchemy models, repositories, Alembic
schemas/           # normalized/features/model_ready JSON contracts
tests/
  stage_two/
  stage_three/
docs/
  ru/
  en/
```

## Entry Points and Routing

Main entrypoint:

```powershell
python manage.py <module> <service> [action] [args]
```

Actual routing:

| Layer | File | Purpose |
| --- | --- | --- |
| `manage.py` | `manage.py` | Thin CLI entrypoint; forwards `stage-three` to the argparse router |
| root router | `scripts/router_script.py` | Dispatches to `handlers`, `stage_two`, `stage_three` |
| Stage One | `scripts/handlers/router_handler.py` | Legacy dataset analysis/sorting handlers |
| Stage Two | `scripts/stage_two/cli.py` | Actual normalization pipeline router |
| Stage Three | `scripts/stage_three/cli.py` | Argparse router for feature/model-ready preparation |

Important: `python manage.py stage-two --help` is not a reliable help source in the current checkout. It prints `unknown Stage Two command` plus the older `config.manage_commands` fallback. The authoritative Stage Two command list is in `scripts/stage_two/cli.py` and `docs/en/normalization/stage_two_commands.md`.

## Stage One

Stage One lives in `scripts/handlers` and performs filesystem-level preparation:

- DNS/Host raw dataset root analysis;
- Host source filtering;
- role/format sorting;
- JSON path map export;
- DNS/Host bucket content analysis reports.

Stage One does not write normalized Parquet and does not register artifacts in the PostgreSQL catalog.

## Stage Two

Stage Two lives in `scripts/stage_two`, `scripts/db`, and `schemas`.

Actual router commands:

- `bootstrap-storage`
- `catalog-ingest`
- `seed-parser-registry`
- `parser-coverage`
- `mark-ready`
- `normalize-format`
- `normalize-all`
- `benchmark-normalization`
- `split-large-files`
- `normalize-dns`
- `normalize-host`
- `run-duckdb-checks`
- `run-leakage-checks`
- `trace-artifact`

Key subsystems:

| Subsystem | Files |
| --- | --- |
| storage bootstrap | `scripts/stage_two/storage/bootstrap.py` |
| catalog ingestion | `scripts/stage_two/ingestion/` |
| parser registry/resolver | `scripts/stage_two/parser_registry/` |
| parsers | `scripts/stage_two/parsers/` |
| normalization runner | `scripts/stage_two/normalization/` |
| execution policy | `scripts/stage_two/execution/` |
| Parquet writer | `scripts/stage_two/parquet/writer.py` |
| DuckDB analytics | `scripts/stage_two/duckdb/service.py` |
| quality/leakage | `scripts/stage_two/quality/` |
| traceability | `scripts/stage_two/traceability/service.py` |

Stage Two owns `raw -> normalized` and must not train models.

## Stage Three

Stage Three lives in `scripts/stage_three`.

Actual commands:

- `validate-inputs`
- `build-feature-catalog`
- `probe-runtime-backend`
- `extract-features`
- `align-labels`
- `build-sequences`
- `build-model-ready`
- `rebalance-dns-supervised`
- `run-quality-checks`
- `run-leakage-checks`
- `trace-artifact`
- `final-report`

Key subsystems:

| Subsystem | Files |
| --- | --- |
| typed CLI requests | `scripts/stage_three/requests.py` |
| storage bootstrap | `scripts/stage_three/storage/bootstrap.py` |
| readiness gate | `scripts/stage_three/readiness/` |
| feature catalog | `scripts/stage_three/feature_catalog/feature_catalog.yml` |
| runtime profiles/backend | `scripts/stage_three/runtime/` |
| extraction | `scripts/stage_three/extraction/` |
| labels/window policies | `scripts/stage_three/labels/` |
| preprocessing | `scripts/stage_three/preprocessing/` |
| model-ready builder | `scripts/stage_three/model_ready/` |
| quality/leakage/traceability | `scripts/stage_three/quality/` |
| final reports/console output | `scripts/stage_three/reports/` |
| DNS supervised split rebuild | `scripts/stage_three/dns_rebalance.py` |

Stage Three is a preparation layer. It creates artifacts for Stage Four but does not train models.

## Feature Catalog

The machine-readable catalog is:

```text
scripts/stage_three/feature_catalog/feature_catalog.yml
```

It defines:

- `forbidden_X_columns`;
- feature groups for DNS, Host, Network, Hybrid, and Sequence;
- source fields and output features;
- dtype/nullability/preprocessing policy.

Core rule: label/source/path/parser/raw/metadata/traceability fields must not enter model-ready X.

## Storage

Actual storage root:

```text
C:\Users\Public\PythonProjects\storage
```

Main zones:

- `parquet/normalized`
- `parquet/features`
- `parquet/model_ready`
- `duckdb/proposal_analytics.duckdb`
- `reports/{ru,en}/stage-one`
- `reports/{ru,en}/stage-two`
- `reports/{ru,en}/stage-three`
- `temp_data`
- `schemas`
- `config`
- `logs`
- `backups`

See `docs/storage.md` for details.

## Tests

Tests are split by stage:

- `tests/stage_two/` - parsers, catalog ingestion, normalization, Parquet writer, DuckDB, leakage, parser reports, status tools.
- `tests/stage_three/` - CLI routing, runtime, feature catalog, extraction, label alignment, preprocessing, model-ready builder, quality/leakage, final report, console output.

Minimum documentation check:

```powershell
git diff --check -- docs
```

Targeted tests after Stage Two/Three code changes:

```powershell
pytest tests/stage_two
pytest tests/stage_three
```

## Invariants

1. Raw datasets are not modified.
2. `TRAIN`, `VALIDATION`, and `TEST` are not mixed.
3. `TEST` is not used for training, preprocessing fit, feature selection, or threshold tuning.
4. Labels are not input features.
5. A missing label does not mean benign.
6. A missing timestamp must not be replaced with current time.
7. Large tables live in Parquet; PostgreSQL stores metadata/status/lineage.
8. `temp_data` is not a source of truth.
9. Stage Four may start only after Stage Three `final-report` returns `READY_FOR_STAGE_FOUR`.

## Gaps

| Area | Status |
| --- | --- |
| Stage Four training/evaluation | Not exposed as CLI |
| RF/XGBoost configs | Proposal-level |
| CNN/LSTM architecture | Proposal-level |
| SHAP/XAI | Proposal-level |
| Late fusion | Proposal-level |
| CV folds/statistical tests/seeds | Need a dedicated experiment config |
| Production Host/Network/Hybrid readiness | Must be checked for each concrete `branch`, `role`, `feature_group`, `experiment_id` |
