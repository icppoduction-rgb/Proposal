# Stage Two Normalization Usage Guide

This document describes the implemented CLI layer: `manage.py` receives `module`, `service`, `action`, and `extra_args`; routes `stage-two` through `scripts.router_script.router_commands()`; and dispatches concrete Stage Two services through `scripts.stage_two.cli.router_stage_two()`.

## Prerequisites

Configure the environment:

```bash
export PATH_DATA_STORAGE=/absolute/path/to/stage-two-storage
export PATH_FOLDER_DATASETS_FILTER=/absolute/path/to/stage-one-filtered-or-sorted-tree
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/database
```

`DATABASE_URL` is loaded by `scripts/db/config.py`. If it is not present in the process environment, the code tries to load `.env` from the repository root.

## Base Run Order

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

This order preserves split separation. Normalization for `TRAIN`, `VALIDATION`, and `TEST` is run as separate commands or through `normalize-all`, which groups files by `branch/role/source_format` and does not merge roles into one output artifact.

## Stage Two Commands

| Command | Purpose | Main output |
| --- | --- | --- |
| `bootstrap-storage` | Creates required directories under `PATH_DATA_STORAGE`. | Storage tree, schema/report/temp/log directories. |
| `catalog-ingest` | Scans `PATH_FOLDER_DATASETS_FILTER` and registers datasets/files. | `datasets`, `ingestion_runs`, `dataset_files`. |
| `seed-parser-registry` | Loads `parser_registry_seed.json` into catalog. | `parser_registry`, `schema_versions`. |
| `parser-coverage [branch]` | Checks parser coverage for registered `branch/role/source_format` combinations. | Console report, parser coverage diagnostics. |
| `mark-ready` | Promotes a selected bucket to `READY_FOR_PARSING`. | Updated `dataset_files.status`. |
| `normalize-format` | Normalizes one `branch/role/source_format`. | `parser_runs`, normalized Parquet, `normalized_artifacts`. |
| `normalize-all` | Normalizes all ready buckets in one branch. | Same outputs, grouped by role/format. |
| `split-large-files` | Splits large line-based files into chunks. | Chunk files, optional catalog registration. |
| `normalize-dns [limit]` | Legacy shortcut for DNS ready files. | Normalized DNS artifacts. |
| `normalize-host [limit]` | Legacy shortcut for Host ready files. | Normalized Host artifacts. |
| `run-duckdb-checks` | Creates DuckDB views over Parquet and runs analytics checks. | DuckDB report, `data_quality_reports`. |
| `run-leakage-checks` | Checks model-ready/feature contracts for leakage. | Leakage reports, `data_quality_reports`. |
| `trace-artifact` | Reconstructs lineage for a model-ready artifact. | Console JSON trace chain. |

## `mark-ready`

Flags:

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

Compact form:

```bash
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
```

Constraints:

- `--dry-run` and `--apply` are mutually exclusive.
- `role` must be one of `TRAIN`, `VALIDATION`, `TEST`.
- The command updates catalog metadata only; it does not modify raw files.

## `normalize-format`

Flags:

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

Compact form:

```bash
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
```

Behavior:

- selects `dataset_files` with status `READY_FOR_PARSING` for the exact `branch/role/source_format`;
- uses `ParserResolver` to select an active parser from `parser_registry`;
- marks selected files as `UNSUPPORTED_FORMAT` when no parser is available;
- writes normalized Parquet and registers `parser_runs`/`normalized_artifacts`;
- uses `ProcessPoolExecutor` when `--workers > 1`;
- skips files with existing successful normalized artifacts when `--resume` is enabled.

`--packet-mode` supports:

| Value | Purpose |
| --- | --- |
| `packet-summary` | Safe mode for packet captures: summary-level parsing. |
| `dns-only` | Extract DNS events from packet captures where the parser supports it. |
| `sample` | Process a sample of packets; requires `--sample-size`. |

## `normalize-all`

```bash
python manage.py stage-two normalize-all \
  --branch dns \
  --limit 1000 \
  --workers 2 \
  --resume
```

Compact form:

```bash
python manage.py stage-two normalize-all dns:1000
```

The command selects ready groups inside one branch and invokes `NormalizeFormatRunner` per group. Grouping is by `role` and `source_format`, which prevents `TRAIN`, `VALIDATION`, and `TEST` from being mixed.

## Legacy Commands

```bash
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

These commands remain for compatibility. For reproducible runs, prefer `normalize-format` or `normalize-all` because they explicitly define branch/role/format and performance options.

## Large-File Splitting

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TRAIN \
  --format csv \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Purpose: prepare large line-based files for normalization. The command supports `csv`, `pcap.csv`, `txt`, `json`, `json-1`, log formats, `sc`, `ghc`, `netflow_day`, `netflow_ids`, `wls_day`, and metricbeat-like logs. Binary formats (`cap`, `pcap`, `pcapng`, `bson`) are not split by this splitter.

Rules:

- `--register` is valid only together with `--apply`;
- without `--apply`, the command is a dry run;
- chunks are written under `PATH_FOLDER_DATASETS_FILTER/chunked/...`;
- registered chunks receive status `READY_FOR_PARSING`;
- the source file may be marked `SKIPPED` unless `--keep-source-ready` is used.

## Checks

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

`run-duckdb-checks` creates `normalized_all`, `features_all`, and `model_ready_all` views over Parquet and checks row counts, required columns, split contamination, and schema mismatch. `run-leakage-checks` checks forbidden X columns, absence of `TEST` from training/preprocessing fit, and registers CRITICAL violations.

## Trace Artifact

```bash
python manage.py stage-two trace-artifact 123
python manage.py stage-two trace-artifact parquet/model_ready/tabular/dns/TRAIN/schema=v1/X_train.parquet
```

A numeric argument is interpreted as `model_ready_artifacts.id`; a string path is interpreted as `model_ready_artifacts.artifact_path`. The command requires a `feature_artifact_id` on the model-ready artifact and a `normalized_artifact_id` on the feature artifact; otherwise the traceability chain is considered broken.

## Module Checks

These checks are not registered as `manage.py stage-two` commands, but they are implemented as Python modules:

```bash
python -m scripts.db.smoke_check
python -m scripts.stage_two.readiness_check
python -m scripts.stage_two.e2e_dry_run
```

`readiness_check` verifies migrations, storage paths, catalog table counts, parser coverage, normalized/feature/model-ready registration, quality/leakage reports, traceability, and raw file hashes. `e2e_dry_run` creates synthetic DNS/Host samples under `temp_data`, runs ingestion, seed, normalization, feature/model-ready registry services, DuckDB/leakage checks, and traceability.

## Typical Errors

| Symptom | Cause | Action |
| --- | --- | --- |
| `DATABASE_URL must be configured` | `DATABASE_URL` is not set in environment or `.env`. | Configure `DATABASE_URL`. |
| `PATH_DATA_STORAGE must be configured` | Storage root is not set. | Set `PATH_DATA_STORAGE`, then run `bootstrap-storage`. |
| `No parser available` / `UNSUPPORTED_FORMAT` | No active parser in `parser_registry` for `branch/role/source_format`. | Check `parser-coverage`, add a parser or registry entry. |
| Empty DuckDB views | Parquet layer is empty or paths were not created. | Check `normalized_artifacts` and storage paths. |
| Leakage CRITICAL | X artifact contains label/source fields or TEST participates in fit/training. | Rebuild the artifact with the correct contract. |
