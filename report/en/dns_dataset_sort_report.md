# Report: DNS dataset format sorting (stage 6)

## Task description
Implemented DNS dataset sorting by file formats using input JSON files:
- `dns-file.json`
- `dns-path-file.json`

Files are grouped by dataset roles (`TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`) and by format inside `PATH_DNS_DATASETS_FILTER`.

## Added files
- `scripts/handlers/sort_dns_dataset_handler.py`
- `report/ru/dns_dataset_sort_report.md`
- `report/en/dns_dataset_sort_report.md`

## Changed files
- `manage.py`

## Run command
- `python manage.py dns dataset sort`

Additional alias command is supported:
- `python manage.py dataset dns sort`

`manage.py` is an entrypoint only. Core sorting logic is implemented in `scripts/handlers/sort_dns_dataset_handler.py`.

## Sorting directory structure
Created structure:

```text
PATH_DNS_DATASETS_FILTER/
  TRAIN/
    csv/
    pcap/
    pcap.csv/
  TEST/
    csv/
  VALIDATION/
    pcap/
    txt/
  EXPERIMENTS/
```

## Supported formats
Supported format groups:
- `csv`
- `pcap`
- `pcap.csv`
- `txt`

If a non-standard filename appears, extension-based fallback grouping is applied.

## Format detection logic
1. `.pcap.csv` suffix -> `pcap.csv` group.
2. `.pcap` suffix -> `pcap` group.
3. `.csv` suffix -> `csv` group.
4. `.txt` suffix -> `txt` group.
5. Otherwise, file suffix is used as fallback group name.

## Data safety
- Source DNS datasets are not modified.
- Files are not moved or deleted.
- Files are materialized via hardlink; if hardlink fails, safe fallback is `copy2`.
- On filename collisions, deterministic hash suffix is used to avoid overwrite.

## Execution result
Summary is saved to `PATH_TEMP_DATA/sort-dns-format-summary.json`.

Latest run metrics:
- `created_links_count`: `0`
- `copied_files_count`: `0`
- `skipped_existing_count`: `35`
- `missing_source_count`: `0`
- `name_mismatch_count`: `0`

This confirms idempotent behavior: repeated execution reuses existing sorted files without duplication or overwrite.
