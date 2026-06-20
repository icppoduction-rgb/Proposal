# Stage Two Normalization Performance Tuning

Use bounded batches and process workers for large files:

```powershell
python manage.py stage-two normalize-format --branch dns --role TRAIN --format pcap --limit 100 --workers 4 --batch-size 50000 --max-output-part-rows 50000 --packet-mode dns-only --resume
python manage.py stage-two normalize-all --branch host --limit 1000 --workers 4 --batch-size 50000 --max-output-part-rows 50000 --resume
```

## Flags

| Flag | Purpose |
| --- | --- |
| `--workers` | File-level process workers. This uses `ProcessPoolExecutor`, not threads. |
| `--batch-size` | Parser batch size before writing normalized rows. |
| `--max-output-part-rows` | Maximum rows per Parquet part. |
| `--resume` | Reuse the latest resumable parser run and skip already registered part indexes. |
| `--packet-mode` | Packet parsing mode: `packet-summary`, `dns-only`, or `sample`. |
| `--sample-size` | Packet limit for `--packet-mode sample`. |
| `--hash-output-artifacts` | Re-enable output Parquet SHA-256 hashing. Disabled by default for large output speed. |

## Metrics

Per-file metrics are stored in `parser_runs.metadata_json.performance`:

- input size MB;
- rows or packets read;
- emitted events;
- parse, Parquet write, catalog, and total time;
- rows/sec, packets/sec, events/sec, MB/sec;
- peak Python allocation memory;
- output part count.

Each `normalized_artifacts.metadata_json` includes `part_index`, `batch_index`, `rows_in_part`, and checkpoint counters. This keeps traceability intact from raw file to normalized parts and downstream features/model-ready artifacts.

## Operational Notes

`normalize-format` remains scoped to one `branch/role/source_format`. `normalize-all` groups by role and source format inside one branch, so `TRAIN`, `VALIDATION`, and `TEST` are not mixed.

For packet captures, prefer `--packet-mode dns-only` for DNS datasets when non-DNS packet summaries are not needed. Use `sample` with `--sample-size` for parser smoke/performance checks before running multi-GB files.
