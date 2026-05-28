# Report: bugfix for paths in dns-path-file.json

## Brief description
Fixed a bug in the DNS dataset handler: `dns-path-file.json` contained directory paths instead of full file paths.

## Root cause
The `paths_by_role` logic appended `current_path` (directory) instead of `current_path / file_name`.

## What was fixed
- Updated `DNSDatasetHandler`.
- For each discovered file, the handler now stores the full file path in `dns-path-file.json`.
- `dns-file.json` behavior is unchanged: it still stores file names only.

## Changed files
- `scripts/handlers/dns_dataset_handler.py`
- `report/ru/dns_dataset_path_bugfix_report.md`
- `report/en/dns_dataset_path_bugfix_report.md`

## How to verify
1. Run:
```bash
python manage.py dataset dns analyze
```
2. Open `PATH_TEMP_DATA/dns-path-file.json`.
3. Confirm role values contain full file paths (for example `...\\CSV_benign.csv`, `...\\benign.pcap`) instead of directory-only paths.
