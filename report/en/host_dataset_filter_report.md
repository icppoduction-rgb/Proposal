# Report: Host dataset filtering (stage 3)

## Task summary
Implemented Host dataset analysis/filtering stage: from primary scan outputs (`host-path-file.json`, `host-file.json`), only relevant datasets and files are kept for `TRAIN`, `TEST`, `VALIDATION`, and `EXPERIMENTS`.

## Added/changed files
### Added
- `scripts/handlers/filter_host_dataset_handler.py`
- `report/ru/host_dataset_filter_report.md`
- `report/en/host_dataset_filter_report.md`

### Changed
- `manage.py`

## Generated JSON files
Both files are saved into `PATH_TEMP_DATA`:

- `filter-host-path-file.json`  
  Stores paths to required Host datasets by role.
- `filter-host-file.json`  
  Stores required file names by role.

## Excluded files
Files are excluded for these main reasons:

- dataset-role mismatch against project strategy (`dataset_not_allowed_for_role`);
- non-telemetry paths in `Maintainable Log Dataset` (`non_telemetry_path_for_maintainable_dataset`);
- unsupported extensions for training/feature engineering (for example: `.pdf`, `.html`, `.rc`, `.ps1`, `.dmp`, `.webarchive`, `.res`, part of `.pcap`);
- macOS resource-fork artifacts `._*` (`macos_resource_fork_file`).

### Last run summary
- `kept_files_count`: `361646`
- `excluded_files_count`: `30438`

## Filtering logic (short)
1. Read `host-path-file.json` and `host-file.json` from `PATH_TEMP_DATA`.
2. Apply strict dataset role matrix from project docs:
   - `TRAIN`: `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset`
   - `VALIDATION`: `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets`
   - `TEST`: `Unified-Host-Network-Dataset -LANL`, `ISOT-Cloud-IDS-Dataset`, `Dynamic-Malware-Analysis-Dataset`
   - `EXPERIMENTS`: `HDFS-Log-Dataset`
3. Apply dataset-aware path/extension rules:
   - keep syscall/log/telemetry artifacts;
   - remove environment scripts, docs, binaries, and other non-relevant files.
4. Save:
   - `filter-host-path-file.json`
   - `filter-host-file.json`
5. Log every excluded file into `logs/filter.log`.

## Log structure
File: `logs/filter.log`  
Line format:

`timestamp | dataset_type=HOST | role=<ROLE> | dataset=<DATASET_NAME> | reason=<REASON> | path=<FULL_PATH>`

Log includes:
- excluded file path;
- exclusion reason;
- dataset type (`HOST`);
- dataset role.
