# Report: Host dataset format sorting (stage 4)

## Task description
Implemented sorting of filtered Host datasets by file formats.
The handler reads `filter-host-file.json` and `filter-host-path-file.json` from `PATH_TEMP_DATA`, detects each file format using project rules, and builds the target directory structure inside `PATH_HOST_DATASETS_FILTER`.

## Added files
- `scripts/handlers/sort_host_dataset_handler.py`
- `report/ru/host_dataset_sort_report.md`
- `report/en/host_dataset_sort_report.md`

## Changed files
- `manage.py`

## Run command
- `python manage.py host dataset sort`

`manage.py` remains an entrypoint only; all business logic is implemented in `scripts/handlers/sort_host_dataset_handler.py`.

## Sorting structure
The handler always creates role sections:
- `TRAIN`
- `TEST`
- `VALIDATION`
- `EXPERIMENTS`

Then it creates format folders inside each role, for example:

```text
PATH_HOST_DATASETS_FILTER/
  TRAIN/
    csv/
    ghc/
    txt/
    auth.log/
    process.summary.log/
    log-1/
    mainlog-1/
    pcap/
  TEST/
    txt/
    bson/
    json/
    log/
    netflow_day/
    wls_day/
  VALIDATION/
    cap/
    pcap/
    pcapng/
  EXPERIMENTS/
    csv/
    log/
    npz/
```

## Supported format groups
Supported categories include:
- regular extensions (`csv`, `txt`, `ghc`, `sc`, `json`, `log`, `npz`, `bson`, `pcap`, `pcapng`, `cap`, `xml`, `netflow_ids`);
- semantic host log groups (`auth.log`, `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `syslog.log`, `uptime.log`);
- rotated logs (for example, `log.1 -> log-1`, `mainlog.1 -> mainlog-1`);
- `pcap.<timestamp>` files (including `log.pcap.<timestamp>`) mapped to `pcap`;
- non-standard patterns: `messages`, `messages.1`, `journal~`, `netflow_day-*`, `wls_day-*`.

## Format detection logic
1. Apply special-pattern rules first: `netflow_day-*`, `wls_day-*`, `journal~`, `messages`, `mainlog`, rotations (`*.1`, `*.2`, ...), and `pcap.<timestamp>`.
2. For system logs, keep semantic names (`auth.log`, `process.summary.log`, etc.) even when filenames contain date/host prefixes.
3. For all other files, fall back to extension-based grouping.
4. On destination name collisions, apply deterministic hash suffixes to prevent overwrite.

## Data safety guarantees
- Original datasets are not modified.
- No source files are moved or deleted.
- Primary materialization mode is hardlink (no source mutation, no data duplication).
- If hardlink is unavailable, safe fallback is file copy.

## Execution result
Summary is saved to `PATH_TEMP_DATA/sort-host-format-summary.json`.

Key metrics from the last run:
- `created_links_count`: `0`
- `copied_files_count`: `0`
- `skipped_existing_count`: `361646`
- `missing_source_count`: `0`
- `name_mismatch_count`: `0`

This confirms idempotent behavior: repeated execution reuses the existing sorted structure without overwriting and without source data mutation.
