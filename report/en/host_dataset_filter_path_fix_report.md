# Report: `filter-host-path-file.json` fix (file paths)

## Issue summary
`filter-host-path-file.json` stored dataset root folders instead of concrete file paths.  
This violated the filtering stage contract where file-level paths are required.

## Root cause
In `HostDatasetFilterHandler`, after passing filters, the code appended `dataset_root` instead of the original file `raw_path`.

## What was changed
- File: `scripts/handlers/filter_host_dataset_handler.py`
  - In `filter_and_save()` path accumulation was changed:
    - before: dataset root path was added;
    - now: full file path is added (`raw_path`).
  - Removed no-longer-needed dataset-root extraction helper (`_extract_dataset_root`).
  - Result field renamed:
    - `dataset_paths_by_role` → `file_paths_by_role`.

## Verification
1. Command executed:
   - `python manage.py host dataset filter`
2. Output checked:
   - `temp_data/filter-host-path-file.json`
3. Result:
   - role sections now contain file-level paths (for example, `...UAD-Adduser-10-1371.txt`) instead of dataset folder paths.

## Current state after fix
- `filter-host-path-file.json` contains file paths.
- `filter-host-file.json` still contains filtered file names.
- Exclusion log is still written to `logs/filter.log`.
