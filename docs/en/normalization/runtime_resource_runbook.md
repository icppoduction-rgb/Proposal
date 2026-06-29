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

## Performance Runbook for the Current Workstation

Target hardware:

- Intel Core i7-14700KF.
- 64 GB DDR5 RAM.
- Samsung M.2 SSD 2 TB.
- MSI GeForce RTX 5060 Ti 16 GB.

Raw normalization is CPU-oriented. GPU is not enabled for raw parsers by default; keep GPU for feature/model-ready/training work unless a parser-specific backend is implemented and validated.

### Target

- Full Stage Two normalization target: `17 GB <= 3 hours`.
- Required throughput: about `5.67 GB/hour`.
- Expected target for line-based formats on this hardware: `10-20+ GB/hour` after benchmark validation.

### Safe Operational Sequence

1. Run parser coverage and mark one exact bucket ready.
2. Run `benchmark-normalization` on 5-10% of files.
3. Start with `safe` or `balanced`.
4. Move to `fast` only after parser reports, DuckDB checks, leakage checks, RAM, DB connections, and SSD write behavior look healthy.
5. Use `aggressive` only for line-based formats after a clean `fast` run.
6. Run the full bucket with `--resume`.
7. Run post-run gates:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

### Example Commands

Benchmark:

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Line-based full run:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --resume
```

PCAP safe run:

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume
```

BSON safe run:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

### Troubleshooting Performance Runs

| Issue | What to check | Recovery |
| --- | --- | --- |
| PostgreSQL timeout | long transactions, locks, slow catalog writes | lower `--workers`, use `safe`, rerun with `--resume` |
| too many DB connections | process workers vs DB pool size | cap workers to `4-8`, avoid `aggressive`, verify worker-local sessions |
| memory pressure | batch size, output part rows, binary formats | reduce `--batch-size`, reduce `--max-output-part-rows`, split line-based files |
| SSD throttling | high concurrent writes, temperature, hashing | reduce workers, disable output hashing during iterations, stagger large buckets |
| too many small files | scheduler and catalog overhead | keep bounded execution, group by exact format, avoid mixed all-branch runs |
| parser errors | parser run reports, error samples, malformed rows | fix parser/schema handling; do not mark malformed rows successful silently |
| empty DuckDB views | missing Parquet roots or wrong storage path | verify `PATH_DATA_STORAGE`, artifact paths, and `run-duckdb-checks` report |
| leakage critical | forbidden X columns or TEST in training artifacts | stop training use, inspect leakage report, rebuild feature/model-ready artifacts |

### Safety Rules

- Never edit raw dataset files.
- Do not mix `TRAIN`, `VALIDATION`, and `TEST`.
- Do not use `TEST` for training, preprocessing fit, scaler/encoder fit, feature selection, or threshold tuning.
- Keep PostgreSQL as catalog/control plane and Parquet as the large-data store.
- Keep labels and path/source/scenario fields out of model-ready X.
- Do not treat missing labels as benign.
- Do not replace missing timestamps with current time.
- Preserve traceability from raw file to normalized, features, and model-ready artifacts.
