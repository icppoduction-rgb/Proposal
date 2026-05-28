# Report: Host dataset analysis (stage 1)

## Brief description of completed task
Implemented stage 1 for Host dataset analysis: scanning files under the Host datasets directory, assigning roles (`TRAIN`, `TEST`, `VALIDATION`), and saving structure metadata to JSON files.

## Added or modified files
### Added
- `scripts/handlers/host_dataset_handler.py`
- `report/ru/host_dataset_analysis_report.md`
- `report/en/host_dataset_analysis_report.md`

### Modified
- `manage.py`
- `.env.example`

## Commands added to manage.py
Added a dedicated Host analysis command:

```bash
python manage.py host dataset analyze
```

## JSON files created
- `host-path-file.json` — full paths to discovered Host dataset files grouped by role.
- `host-file.json` — file names grouped by role.

Role structure in both JSON files:
- `TRAIN`
- `TEST`
- `VALIDATION`

## Where results are stored
Both JSON files are stored in the directory from `PATH_TEMP_DATA`.

## Short logic overview
1. `manage.py` receives `host dataset analyze` and calls `HostDatasetHandler`.
2. The handler reads `PATH_HOST_DATASETS` and recursively scans files.
3. A role is assigned using path token keywords (`train/test/validation/experiment`).
4. It builds:
   - `host-path-file.json` with full file paths;
   - `host-file.json` with file names.
5. Results are deduplicated, sorted, and written into `PATH_TEMP_DATA`.
