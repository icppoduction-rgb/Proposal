# Normalization Performance Tuning

This document describes only implemented runtime options from `scripts/stage_two/normalization/options.py` and `scripts/stage_two/cli.py`.

## Normalization Options

| CLI option | Default | Purpose |
| --- | --- | --- |
| `--workers` | `STAGE_TWO_DEFAULT_WORKERS` (`1`) | Number of parallel worker processes for `normalize-format`/`normalize-all`. |
| `--batch-size` | `STAGE_TWO_DEFAULT_BATCH_SIZE` (`50000`) | Batch size for parser batch processing. |
| `--max-output-part-rows` | `STAGE_TWO_MAX_OUTPUT_PART_ROWS` (`50000`) | Maximum rows in one output part when the service splits output. |
| `--resume` | `false` | Skip files that already have successful normalized artifacts. |
| `--hash-output-artifacts` | `false` | Compute SHA-256 for output Parquet artifacts. |
| `--packet-mode` | `packet-summary` | Packet parsing mode: `packet-summary`, `dns-only`, `sample`. |
| `--sample-size` | unset | Required for `--packet-mode sample`. |
| `--resource-profile` | unset | Optional preset: `safe`, `balanced`, `fast`, or `aggressive`. |
| `--engine` | `cpu` | Accepted values are `cpu`, `gpu`, `auto`; raw Stage Two parsers still run on CPU unless a parser-specific backend is implemented. |

Resolution order:

1. Start with constants from `config.py`.
2. Apply `--resource-profile` values when a profile is provided.
3. Apply explicit CLI overrides such as `--workers` and `--batch-size`.
4. For `normalize-format` and `benchmark-normalization`, apply format policy for values that were not explicitly overridden.

`normalize-all` resolves the shared runtime options from defaults/profile/explicit flags, but the current CLI route does not apply per-format policy to each group before calling the runner.

Example:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format auth.log \
  --limit 10000 \
  --workers 4 \
  --batch-size 50000 \
  --max-output-part-rows 50000 \
  --resume
```

## Choosing `--workers`

`--workers > 1` enables `ProcessPoolExecutor` in the normalization runner. This helps with independent files, but increases:

- number of open DB connections;
- disk contention;
- memory pressure on large parser outputs;
- parser error diagnosis complexity.

Practical sequence:

1. Start with `--workers 1 --limit 10`.
2. Check parser status, Parquet output, and DuckDB checks.
3. Increase workers gradually.
4. For binary PCAP/PCAPNG, do not increase workers without monitoring RAM/IO.

## Packet Modes

| Mode | When to use |
| --- | --- |
| `packet-summary` | Default safe summary parsing for packet captures. |
| `dns-only` | DNS extraction from packet captures when supported by the parser. |
| `sample` | Initial assessment of large PCAP/PCAPNG; requires `--sample-size`. |

If `packet-mode = sample` and `sample-size` is not set, option validation raises an error.

## Large-File Splitting

For large line-based files:

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TRAIN \
  --format csv \
  --max-part-size-mb 512 \
  --apply \
  --register
```

The splitter supports text/line formats and is not intended for `cap`, `pcap`, `pcapng`, or `bson`.

Risks:

- JSON arrays/objects may be unsafe for line splitting;
- header handling should be verified with `--header auto|yes|no`;
- chunks do not appear in catalog unless `--register` is used.

## Output Hashing

`--hash-output-artifacts` improves verifiability but adds IO cost because the file must be read after writing. It can remain disabled for smoke/iteration; enable it for final artifacts.

## Resume

`--resume` skips files that already have successful normalized artifacts. It does not replace data quality checks. After resume, still run:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
```

## Limitations

- Performance options must not change contracts or labels.
- Roles must not be merged for speed.
- Do not use `TEST` to tune batch/feature/preprocessing decisions when that affects the training pipeline.
- For mixed CSV/JSON schemas, reduce batch size and start with `--limit`.

## Performance Architecture Update

Stage Two now supports resource profiles, format-specific policy, bounded multiprocessing, streaming parser batches, chunk-aware large-file processing, atomic Parquet writes, benchmark reports, and post-run quality gates.

### Performance Target

- Dataset target: `17 GB <= 3 hours`.
- Required throughput: about `5.67 GB/hour`.
- Target throughput on the current workstation: `10-20+ GB/hour` for line-based formats when parser errors, RAM pressure, PostgreSQL load, and SSD throttling are under control.

Reference workstation:

- CPU: Intel Core i7-14700KF.
- RAM: 64 GB DDR5.
- Storage: Samsung M.2 SSD 2 TB.
- GPU: MSI GeForce RTX 5060 Ti 16 GB.

GPU is reserved for feature/model-ready/training layers. Raw normalization parsers run on CPU by default; do not move PCAP/BSON/raw log parsing to GPU unless a dedicated backend is implemented and validated.

### Resource Profiles

Use `--resource-profile safe|balanced|fast|aggressive` with `normalize-format`, `normalize-all`, and `benchmark-normalization`.

| Profile | workers | batch_size | max_output_part_rows | packet_batch_size | hash_output_artifacts |
| --- | ---: | ---: | ---: | ---: | --- |
| `safe` | 4 | 50000 | 100000 | 50000 | false |
| `balanced` | 8 | 100000 | 250000 | 50000 | false |
| `fast` | 12 | 200000 | 500000 | 50000 | false |
| `aggressive` | 14 | 300000 | 750000 | 50000 | false |

CLI arguments override profile values. Example: `--resource-profile fast --workers 6` resolves to `workers=6` and the remaining values from `fast`.

The CLI prints `resolved_runtime_settings` before normalization. Treat `aggressive` warnings as operational warnings: monitor RAM, DB connections, parser failures, and SSD temperature/throttling.

### Format Policy

When explicit CLI values are not provided, `normalize-format` and `benchmark-normalization` apply a format policy after resource profile resolution:

- line-based fast formats (`txt`, `sc`, `ghc`, log/syslog/messages/mainlog, `wls_day`, metric logs): higher workers and larger batches;
- CSV / `pcap.csv` / NetFlow: moderate-high workers and large batches;
- JSON / JSONL (`json`, `json-1`): moderate workers and batches;
- BSON: low workers;
- PCAP / PCAPNG / CAP: low workers, `packet_batch_size=50000`, default `packet_mode=packet-summary`.

Explicit CLI values still win over policy. `normalize-all` should be run with conservative explicit settings or a conservative profile when the ready groups include mixed/risky formats.

### Recommended Sequence

1. Mark one exact bucket ready: one `branch/role/source_format`.
2. Benchmark 5-10% of the data with `--dry-run` first, then a small actual run.
3. Start with `safe` or `balanced`.
4. Move to `fast` only after DuckDB checks, leakage checks, parser error samples, RAM, DB connections, and SSD metrics look healthy.
5. Use `aggressive` only for line-based formats after the same checks are clean.
6. Run full normalization with `--resume`.
7. Run DuckDB, leakage, and readiness checks.

### Commands

Benchmark 5-10%:

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Split a large line-based file:

```bash
python manage.py stage-two split-large-files \
  --branch host \
  --role TEST \
  --format txt \
  --max-part-size-mb 512 \
  --apply \
  --register
```

Line-based fast normalization:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --resume
```

PCAP with safe settings:

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

BSON with safe settings:

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

Post-run checks:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

### Safety Invariants

- Raw files are not modified.
- `TRAIN`, `VALIDATION`, and `TEST` are not mixed in catalog records, Parquet paths, features, or model-ready artifacts.
- `TEST` is never used for training, preprocessing fit, scaler/encoder fit, feature selection, or threshold tuning.
- PostgreSQL is the control plane; large normalized/features/model-ready data remains in Parquet.
- Labels and source/path/scenario/dataset role fields are not model-ready X features.
- Missing labels are not benign labels.
- Missing timestamps are represented as null / `timestamp_type=missing` / `event_order`, never current time.
- Parser errors remain explicit: `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `SKIPPED`, `UNSUPPORTED_FORMAT`.
- Traceability must remain `raw -> normalized -> features -> model-ready`.

### Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| PostgreSQL timeout | too many workers or slow catalog updates | reduce `--workers`, use `safe`, check DB pool/locks, rerun with `--resume` |
| too many DB connections | `workers` exceeds DB capacity | cap workers at `4-8`, avoid `aggressive`, verify each worker opens its own session |
| memory pressure | batch/output parts too large or binary parser load | reduce `--batch-size` and `--max-output-part-rows`; split line-based files |
| SSD throttling | too many concurrent writes or hashing | reduce workers, keep `--hash-output-artifacts` off during iteration, check SSD temperature |
| too many small files | future submission pressure and DB overhead | rely on bounded executor; batch by exact format; keep `--resume` enabled |
| parser errors | malformed rows or unsupported schema variant | inspect parser run report and error samples; do not hide failed rows |
| empty DuckDB views | no Parquet files, wrong `PATH_DATA_STORAGE`, or failed normalization | run `bootstrap-storage`, inspect artifact paths, rerun `run-duckdb-checks` |
| leakage critical | forbidden X columns or TEST contamination | block artifact use, inspect `run-leakage-checks` report, rebuild features/model-ready |
