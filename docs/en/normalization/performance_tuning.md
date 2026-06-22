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
