# Runtime Resource Runbook

This runbook describes Stage Two normalization diagnostics without modifying raw files.

## Quick Status Checklist

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

## Storage Is Not Ready

Symptoms:

- `PATH_DATA_STORAGE must be configured`;
- missing directories in readiness report;
- DuckDB views are empty because Parquet roots do not exist.

Actions:

```bash
export PATH_DATA_STORAGE=/absolute/path/to/stage-two-storage
python manage.py stage-two bootstrap-storage
python -m scripts.stage_two.readiness_check
```

## Catalog Is Empty

Symptoms:

- `catalog_counts.dataset_files = 0`;
- `parser-coverage` has nothing to check;
- `mark-ready` finds no files.

Actions:

```bash
export PATH_FOLDER_DATASETS_FILTER=/absolute/path/to/stage-one-filtered-or-sorted-tree
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
```

Check that the input tree contains `TRAIN`, `VALIDATION`, and `TEST`; the scanner does not activate arbitrary roles.

## Parser Is Missing

Symptoms:

- `UNSUPPORTED_FORMAT`;
- `parser-coverage` shows an uncovered combination;
- `normalize-format` does not create a normalized artifact.

Actions:

1. Check `branch/role/source_format` in `dataset_files`.
2. Check `parser_registry` after `seed-parser-registry`.
3. Add a parser class or registry entry.
4. Rerun:

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --apply
```

## Normalization Fails

Run:

```bash
python manage.py stage-two normalize-format \
  --branch <branch> \
  --role <ROLE> \
  --format <format> \
  --limit 10 \
  --workers 1
```

After the error, check:

- `parser_runs.status`, counters, error samples;
- `dataset_files.status` and `error_message`;
- parser-specific warnings;
- schema mismatch report;
- file size and whether `split-large-files` is needed.

For large line-based files:

```bash
python manage.py stage-two split-large-files \
  --branch <branch> \
  --role <ROLE> \
  --format <format> \
  --max-part-size-mb 512 \
  --apply \
  --register
```

## DuckDB Checks Failed

Check:

- Parquet files exist under `PATH_DATA_STORAGE/parquet`;
- catalog paths match files on disk;
- required columns exist;
- roles are not mixed;
- empty artifacts were not written instead of parser errors.

Run:

```bash
python manage.py stage-two run-duckdb-checks
```

## Leakage Checks Failed

Check:

- model-ready `X` does not contain forbidden columns;
- preprocessing artifacts have `fitted_on_role = TRAIN`;
- `TEST` is not used in training context;
- unlabeled events are not turned into benign.

Run:

```bash
python manage.py stage-two run-leakage-checks
```

A CRITICAL leakage report must block artifact use.

## Traceability Chain Is Broken

Run:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
python -m scripts.stage_two.readiness_check
```

Check links:

```text
model_ready -> feature -> normalized -> parser_run -> dataset_file -> dataset
```

If `feature_artifact_id` or `normalized_artifact_id` is missing, the artifact is not fully traceable.

## Raw Hash Mismatch

Readiness check recalculates hashes for `dataset_files.file_path`. A mismatch means the raw file changed after ingestion or the catalog points to the wrong file.

Actions:

1. Do not overwrite catalog manually without audit.
2. Check source path and backup.
3. Rerun `catalog-ingest` if the raw tree was officially updated.
4. Rebuild downstream artifacts because normalized/features/model-ready artifacts may have been produced from older content.
