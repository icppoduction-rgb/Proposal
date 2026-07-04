# Stage Two Normalization Commands

This document describes the implemented Stage Two normalization commands and the operational run order. Verified sources: `manage.py`, `scripts/router_script.py`, `scripts/stage_two/cli.py`, `scripts/stage_two/*` services, and `stage_two_dns_host_normalization_commands.txt`.

Main entry point:

```bash
python manage.py stage-two <command> [args]
```

`manage.py` receives `module`, `service`, `action`, and `extra_args`; `scripts/router_script.py` routes `module=stage-two` to `scripts.stage_two.cli.router_stage_two()`. Unknown Stage Two commands return `unknown Stage Two command`.

Code sync note, checked on 2026-07-04: the fallback text printed by `config.manage_commands` is not a complete Stage Two help screen. It omits newer router commands such as `parser-coverage`, `mark-ready`, `normalize-format`, `normalize-all`, `benchmark-normalization`, and `split-large-files`. Treat `scripts/stage_two/cli.py` as the source of truth for implemented commands.

## Full Run Order

```bash
python manage.py stage-two bootstrap-storage
alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage

# Operational step: select a bucket and prepare only the required branch/role/format.
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply

# Optional benchmark before a full run.
python manage.py stage-two benchmark-normalization --branch dns --role TRAIN --format csv --limit 1000 --sample-ratio 0.10 --dry-run

# Main precise production/runbook command.
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 100 --workers 1 --resume

# Legacy shortcuts when all ready DNS or Host files should be processed.
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10

python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

`TRAIN`, `VALIDATION`, and `TEST` are run as separate bucket commands or through `normalize-all`, which groups work by `role/source_format`. `TEST` is not used for training, preprocessing fit, scaler/encoder fit, feature selection, or threshold tuning.

## Commands and Operational Steps

| Step | Command | Implemented in CLI | Purpose |
| --- | --- | --- | --- |
| 1 | `bootstrap-storage` | Yes | Create the required `PATH_DATA_STORAGE` tree. |
| 2 | `catalog-ingest` | Yes | Register Stage One filtered/sorted files in PostgreSQL Catalog. |
| 3 | `seed-parser-registry` | Yes | Load schema/parser metadata from the seed file. |
| 4 | `parser-coverage [branch]` | Yes | Check parser registry coverage for catalog buckets. |
| 5 | `mark-ready` | Yes | Promote selected files to `READY_FOR_PARSING`. |
| 6 | `split-large-files` | Yes | Split large line-based ready files into chunks. |
| 7 | `normalize-format` | Yes | Normalize one `branch/role/source_format`. |
| 8 | `normalize-all` | Yes | Normalize all ready buckets inside one `dns` or `host` branch. |
| 9 | `benchmark-normalization` | Yes | Benchmark one exact `branch/role/source_format` bucket and estimate throughput. |
| 10 | `normalize-dns [limit]` | Yes | Legacy shortcut for DNS files in `READY_FOR_PARSING`. |
| 11 | `normalize-host [limit]` | Yes | Legacy shortcut for Host files in `READY_FOR_PARSING`. |
| 12 | `run-duckdb-checks` | Yes | Create DuckDB views and save analytics report. |
| 13 | `run-leakage-checks` | Yes | Check model-ready/feature contracts for leakage. |
| 14 | `trace-artifact` | Yes | Reconstruct lineage for a model-ready artifact. |
| - | `readiness_check`, `e2e_dry_run` | Not as `manage.py stage-two` | Run as Python modules. |

## `bootstrap-storage`

```bash
python manage.py stage-two bootstrap-storage
```

**What it does:** idempotently creates required Stage Two directories under `PATH_DATA_STORAGE`: `postgres/`, `pgadmin/`, `parquet/normalized/`, `parquet/features/`, `parquet/model_ready/`, `duckdb/sql/`, `duckdb/exports/`, `logs/stage-two/`, `backups/`, `temp_data/`, `schemas/`, `reports/ru/stage-two/`, `reports/en/stage-two/`, `config/`.

**When to run:** once during environment setup and again after storage contract changes. Re-running does not delete existing files.

**Inputs:** `PATH_DATA_STORAGE`.

**Artifacts:** storage directories. No Parquet files or reports are created in this step.

**PostgreSQL:** does not read or write tables.

**Possible errors:** `PATH_DATA_STORAGE must be configured before bootstrapping storage`, directory permission errors.

**How to verify:** CLI prints `root`, `created_count`, and `existing_count`; required directories exist on disk.

## `catalog-ingest`

```bash
python manage.py stage-two catalog-ingest
```

**What it does:** scans `PATH_FOLDER_DATASETS_FILTER`, infers `branch`, `role`, and `source_format`, computes size, mtime, and SHA-256, then registers datasets/files in PostgreSQL Catalog. Raw files are not modified.

**When to run:** after the Stage One sorted/filter tree exists and whenever new or changed files appear.

**Inputs:** `PATH_FOLDER_DATASETS_FILTER`, available database, applied Alembic migrations.

**Artifacts:** no external Parquet artifacts.

**PostgreSQL:** writes `ingestion_runs`, `datasets`, and `dataset_files`. New supported non-empty files receive `REGISTERED`; empty files receive `EMPTY_FILE`; scanner-unsupported formats receive `UNSUPPORTED_FORMAT`; changed files are counted in `files_changed`.

**Possible errors:** missing `PATH_FOLDER_DATASETS_FILTER`, database connection failure, file read error, hash/stat failure.

**How to verify:** CLI prints `run_count` and run summaries with `SUCCESS` or `PARTIAL_SUCCESS`; `dataset_files` contains rows for the required `branch/role/source_format`.

## `seed-parser-registry`

```bash
python manage.py stage-two seed-parser-registry
```

**What it does:** loads schema metadata and parser registry entries from `scripts/stage_two/parser_registry/parser_registry_seed.json`.

**When to run:** after migrations and before `mark-ready`/normalization. Re-running updates existing registry entries.

**Inputs:** seed JSON, available parser classes in `scripts/stage_two/parsers/*`, database connection.

**Artifacts:** no file artifacts.

**PostgreSQL:** writes/updates `schema_versions` and `parser_registry`.

**Possible errors:** invalid seed, missing parser module/class, database error.

**How to verify:** CLI prints `schema_version_id`, `inserted`, and `updated`; `parser-coverage` shows `parser_active=yes` for supported buckets.

## `parser-coverage`

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage dns
python manage.py stage-two parser-coverage host
```

**What it does:** builds a `branch/role/source_format` matrix from catalog counts and `parser_registry`, then verifies whether an active parser exists and whether its parser class is importable.

**When to run:** after `catalog-ingest` and `seed-parser-registry`, and before bulk `mark-ready`.

**Inputs:** `dataset_files`, `datasets`, `parser_registry`, Stage One path JSON only for diagnostics.

**Artifacts:** parser coverage reports through `scripts.stage_two.reports.parser_reports`.

**PostgreSQL:** reads `datasets`, `dataset_files`, `parser_registry`; does not update file statuses.

**Possible errors:** unknown branch, invalid parser class, empty catalog, catalog/registry mismatch.

**How to verify:** result payload has `status=SUCCESS`; rows with real files have `parser_active=yes`. If `catalog_gap_rows` or `missing_parser_rows` is greater than zero, fix registry/parser coverage first.

## Operational `READY_FOR_PARSING` Step

Preparation for `READY_FOR_PARSING` is implemented by `mark-ready`. If this command is not used, the same transition is a manual catalog operation and must only be done after parser coverage has been checked.

```bash
python manage.py stage-two mark-ready --branch host --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format csv --apply
```

Compact form:

```bash
python manage.py stage-two mark-ready dry-run:host:TRAIN:csv
python manage.py stage-two mark-ready apply:host:TRAIN:csv
```

**What it does:** selects files in the active source group for an exact `branch/role/source_format`, checks the parser resolver, and promotes eligible rows to `READY_FOR_PARSING`.

**When to run:** after `parser-coverage`, separately for each required bucket. Run `--dry-run` first, then `--apply`.

**Inputs:** `--branch`, `--role`, `--format`; parser registry entry for the bucket.

**Artifacts:** JSON/Markdown reports in `reports/{ru,en}/stage-two/status/` when `PATH_DATA_STORAGE` is configured.

**PostgreSQL:** reads `datasets`, `dataset_files`, `parser_registry`; updates `dataset_files.status` to `READY_FOR_PARSING` only for eligible files. Default eligible statuses: `REGISTERED`, `CHANGED`, `DISCOVERED`. With `--retry-failed`, eligible statuses are `FAILED`, `SKIPPED`, `PARTIALLY_PARSED`.

**Possible errors:** missing parser (`UNSUPPORTED_FORMAT`), invalid role, simultaneous `--dry-run` and `--apply`, empty `--format`, ineligible current statuses (`PARSED`, `EMPTY_FILE`, `READY_FOR_PARSING`, etc.).

**How to verify:** `dry_run=false`, `status=SUCCESS`, `updated > 0`; the report shows `<previous_status> -> READY_FOR_PARSING` transitions.

## `split-large-files`

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

**What it does:** splits large line-based files in `READY_FOR_PARSING` into chunks. Supported formats include `csv`, `pcap.csv`, `txt`, `json`, `json-1`, log formats, `ghc`, `sc`, `netflow_day`, `netflow_ids`, `wls_day`, and metricbeat-like logs. Binary formats (`cap`, `pcap`, `pcapng`, `bson`) are not split by this splitter.

**When to run:** before `normalize-format` when one file is too large for available RAM/time. For DNS TEST csv in the runbook, use `--header no`.

**Inputs:** catalog rows in `READY_FOR_PARSING`, source file on disk, part-size options.

**Artifacts:** chunk files under `PATH_FOLDER_DATASETS_FILTER/chunked/...`.

**PostgreSQL:** with `--register`, registers chunks in `dataset_files` with status `READY_FOR_PARSING`; the source file may be moved to `SKIPPED` unless `--keep-source-ready` is used.

**Host VALIDATION `wls_day`:** the original raw bucket `host/VALIDATION/wls_day` is intentionally excluded after chunk registration. Continue normalization from `chunked/host/VALIDATION/wls_day/...` records only; do not re-promote the original three large files.

**Possible errors:** `--register` without `--apply`, unsupported binary format, missing source file, output directory already exists without `--overwrite`, invalid `--header`.

**How to verify:** CLI prints `status=SUCCESS`, `chunks_created > 0`, `registered > 0`; `normalize-format` then selects chunks rather than the original large file.

## `normalize-format`

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

Compact form:

```bash
python manage.py stage-two normalize-format host:TRAIN:csv:100
```

**What it does:** selects `dataset_files.status=READY_FOR_PARSING` for one `branch/role/source_format`, resolves a parser through the registry, runs the DNS or Host normalization service, writes normalized Parquet parts, and registers artifacts.

**When to run:** the recommended main normalization command, especially for the runbook in `stage_two_dns_host_normalization_commands.txt`, because it explicitly fixes branch, role, and format.

**Inputs:** ready files, parser registry entry, normalized schema version, raw file path, storage root.

**Artifacts:** normalized Parquet:

```text
parquet/normalized/{branch}/{role}/{modality}/{dataset_slug}/schema={schema_version}/part-{run_id}.parquet
```

Parser run reports are also created in `reports/{ru,en}/stage-two/parser/`.

**PostgreSQL:** reads `dataset_files`, `datasets`, `parser_registry`, `schema_versions`; writes `parser_runs`, `normalized_artifacts`; updates `dataset_files.status` to `PARSED`, `PARTIALLY_PARSED`, `FAILED`, or `UNSUPPORTED_FORMAT`.

**Possible errors:** no parser, parser class cannot be imported, file missing, parser error, out of memory, invalid numeric options, `packet_mode` unsupported by the concrete parser.

**How to verify:** CLI prints `status=SUCCESS`, `parsed + partially_parsed > 0`, `failed=0`, `unsupported=0`; Parquet files exist; `normalized_artifacts` contains paths; `parser_runs.status` is not `FAILED`.

## `normalize-all`

```bash
python manage.py stage-two normalize-all \
  --branch host \
  --limit 1000 \
  --workers 2 \
  --batch-size 10000 \
  --max-output-part-rows 50000 \
  --resume
```

Compact form:

```bash
python manage.py stage-two normalize-all host:1000
```

**What it does:** walks ready groups inside one branch and calls `normalize-format` for each `role/source_format` group.

**When to run:** when parser coverage is checked and several ready buckets inside `dns` or `host` should be processed.

**Inputs:** `--branch dns|host`, ready files.

**Artifacts:** same as `normalize-format`, across multiple groups.

**PostgreSQL:** same tables as `normalize-format`; roles are not mixed because each group is processed separately.

**Possible errors:** partial failure in one bucket produces overall `PARTIAL_SUCCESS`; unsupported parser produces `UNSUPPORTED_FORMAT` for that group.

**How to verify:** `groups_count > 0`, `status=SUCCESS`; every group summary has `failed=0`, `unsupported=0`.

## `normalize-dns` and `normalize-host`

```bash
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

**What it does:** legacy shortcut. Selects files with `READY_FOR_PARSING` for `branch=dns` or `branch=host` and runs the corresponding normalization service. The only positional argument is an optional non-negative integer `limit`.

**When to run:** for quick checks or backward compatibility. Prefer `normalize-format` for reproducible batch runs because it explicitly specifies `role/source_format` and exposes performance options.

**Inputs:** ready files for the selected branch.

**Artifacts:** normalized Parquet and catalog records like `normalize-format`.

**PostgreSQL:** writes `parser_runs`, `normalized_artifacts`; updates `dataset_files.status`.

**Possible errors:** more than one argument, non-numeric limit, parser/file errors.

**How to verify:** CLI prints `files_seen`, `normalized`, and `skipped`; for full control, also inspect `parser_runs` and `normalized_artifacts`.

## `run-duckdb-checks`

```bash
python manage.py stage-two run-duckdb-checks
```

**What it does:** creates DuckDB views `normalized_all`, `features_all`, and `model_ready_all` over Parquet and runs analytics checks: row counts, missing required columns, split contamination, and schema mismatch.

**When to run:** after normalization and after feature/model-ready artifacts appear.

**Inputs:** `PATH_DATA_STORAGE`, Parquet layers, DuckDB package.

**Artifacts:** JSON report `reports/en/stage-two/quality/duckdb_analytics_report.json`; DuckDB database path from storage config.

**PostgreSQL:** writes an aggregate report to `data_quality_reports` with `check_group=duckdb`, severity `INFO` or `ERROR`.

**Possible errors:** `PATH_DATA_STORAGE` is not set, DuckDB is not installed, Parquet files are missing or have incompatible schemas.

**How to verify:** CLI prints `status=SUCCESS`, `check_count`, `catalog_report_id`; the report contains no failed checks.

## `run-leakage-checks`

```bash
python manage.py stage-two run-leakage-checks
```

**What it does:** checks leakage rules over DuckDB views and catalog context. Critical rules include banning label/source/trace fields from model-ready X artifacts and preventing `TEST` rows from appearing in training artifacts.

**When to run:** after feature/model-ready artifacts are built and before data is used for training.

**Inputs:** Parquet `features`/`model_ready`, DuckDB views, catalog metadata.

**Artifacts:** leakage reports in `reports/{ru,en}/stage-two/leakage/`.

**PostgreSQL:** writes `data_quality_reports` with `check_group=leakage`; failed leakage checks receive severity `CRITICAL`.

**Possible errors:** empty model-ready views, forbidden X columns, `TEST` contamination, inconsistent roles in artifact paths/columns.

**How to verify:** CLI prints `status=SUCCESS`, severity is not `CRITICAL`, and `check_count`; the report contains no failed leakage checks.

## `trace-artifact`

```bash
python manage.py stage-two trace-artifact 123
python manage.py stage-two trace-artifact parquet/model_ready/tabular/dns/TRAIN/schema=v1/X_train.parquet
```

**What it does:** reconstructs the lineage chain for a model-ready artifact. A numeric argument is treated as `model_ready_artifacts.id`; a string argument is treated as `model_ready_artifacts.artifact_path`.

**When to run:** after model-ready artifacts are created or during quality/leakage investigations.

**Inputs:** model-ready artifact id or path.

**Artifacts:** no files are created; JSON trace chain is printed to stdout.

**PostgreSQL:** reads the chain:

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

**Possible errors:** artifact not found, missing `feature_artifact_id`, missing `normalized_artifact_id`, broken catalog chain.

**How to verify:** command prints JSON containing dataset, source file, parser run, normalized artifact, feature artifact, and model-ready artifact.

## Commands from the Operational Runbook

`stage_two_dns_host_normalization_commands.txt` contains practical batch commands for remaining DNS/Host formats. They map to implemented CLI commands:

- `mark-ready --dry-run/--apply` for each `branch/role/source_format`;
- `split-large-files` for large line-based files;
- `normalize-format` with `--workers`, `--batch-size`, `--max-output-part-rows`, `--packet-mode`, `--sample-size`, `--resume`;
- `parser-coverage`, `run-duckdb-checks`, `run-leakage-checks` as post-run checks.

The file includes Windows-specific `cd` and `conda activate` commands; these are environment instructions, not project CLI commands. `python -m scripts.stage_two.readiness_check` is implemented as a module check, but it is not registered in `router_stage_two`.

## Run Invariants

1. Raw files are not modified; Stage Two creates metadata and new artifacts.
2. `TRAIN`, `VALIDATION`, and `TEST` are processed through separate bucket commands.
3. `TEST` is not used for fit/training/tuning.
4. Labels are not X features.
5. A missing label does not mean benign.
6. A missing timestamp must not be replaced with current time.
7. All artifacts must preserve traceability `raw -> normalized -> features -> model-ready`.

## Performance Commands and Profiles

The current CLI also includes `benchmark-normalization` and resource profiles for `normalize-format` / `normalize-all`.

### `benchmark-normalization`

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Supported options:

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

The report includes `input_bytes`, `processed_bytes`, `processed_gb`, `elapsed_seconds`, `gb_per_hour`, file/row/event rates, failed/partial/skipped/unsupported files, Parquet output size, average parser/write time, `estimated_time_for_17gb`, and `meets_3_hour_target`.

Actual benchmark runs force safe resume behavior when `--dry-run` is not used, so repeated benchmark commands should not duplicate successful normalized artifacts.

### Resource profiles

| Profile | workers | batch_size | max_output_part_rows | packet_batch_size |
| --- | ---: | ---: | ---: | ---: |
| `safe` | 4 | 50000 | 100000 | 50000 |
| `balanced` | 8 | 100000 | 250000 | 50000 |
| `fast` | 12 | 200000 | 500000 | 50000 |
| `aggressive` | 14 | 300000 | 750000 | 50000 |

CLI overrides take priority over profile and format policy. Example:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --workers 6 \
  --resume
```

This resolves `workers=6` and keeps the other values from `fast`, unless the format policy safely caps them for risky formats.

### Safe PCAP/BSON examples

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

### Large line-based files

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TEST \
  --format txt \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Do not split `cap`, `pcap`, `pcapng`, or `bson` with the line splitter.

### Required gates after performance runs

`normalize-format` writes a post-run validation summary. After performance runs, also run:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

If `run-leakage-checks` returns CRITICAL, do not use the affected feature/model-ready artifacts.
