# Report: DNS dataset analysis (stage 1)

## Brief description of completed task
The first stage of DNS dataset analysis was implemented: scanning dataset directories, assigning roles (`TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`), collecting dataset paths and file names, and saving the result into JSON files.

## Added or modified files
### Added
- `scripts/json_data.py`
- `scripts/json-data.py`
- `scripts/handlers/dns_dataset_handler.py`
- `report/ru/dns_dataset_analysis_report.md`
- `report/en/dns_dataset_analysis_report.md`

### Modified
- `manage.py`

## Commands added to manage.py
A dedicated command was added to run DNS dataset analysis:

```bash
python manage.py dataset dns analyze
```

## JSON files created
- `dns-path-file.json` — paths to discovered DNS datasets grouped by role.
- `dns-file.json` — file names inside DNS datasets grouped by role.

Role structure in both JSON files:
- `TRAIN`
- `TEST`
- `VALIDATION`
- `EXPERIMENTS`

## Where results are stored
Both JSON files are written to the directory from the `PATH_TEMP_DATA` environment variable.
If `PATH_TEMP_DATA` is not set, `temp_data` in the project root is used.

## Short logic overview
1. `manage.py` receives `dataset dns analyze` and calls `DNSDatasetHandler`.
2. The handler reads `PATH_DNS_DATASETS` and recursively scans files.
3. Each directory with files is mapped to a role using path token keywords.
4. Paths and file names are deduplicated, sorted, and grouped by role.
5. Data is saved to `dns-path-file.json` and `dns-file.json` via `JsonDataManager`.
