# Report: export sorted Host dataset paths to JSON (stage 5)

## Task description
Implemented a handler that exports paths of sorted Host datasets into JSON.
Data source: `PATH_HOST_DATASETS_FILTER`.
Target file: `PATH_TEMP_DATA/sort-path-host-file.json`.

## Added files
- `scripts/handlers/save_sort_host_path_handler.py`
- `report/ru/host_dataset_save_paths_report.md`
- `report/en/host_dataset_save_paths_report.md`

## Changed files
- `manage.py`

## Run command
- `python manage.py host dataset save-paths`

`manage.py` is used as an entrypoint only. Core logic is implemented in `scripts/handlers/save_sort_host_path_handler.py`.

## JSON structure
Output JSON:

```json
{
  "TRAIN": {
    "format": ["absolute_path_to_file"]
  },
  "TEST": {
    "format": ["absolute_path_to_file"]
  },
  "VALIDATION": {
    "format": ["absolute_path_to_file"]
  },
  "EXPERIMENTS": {
    "format": ["absolute_path_to_file"]
  }
}
```

- First level: dataset role (`TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`).
- Second level: file format (format directory name in sorted structure).
- Value: list of absolute file paths.

## Path grouping logic
1. Scan `PATH_HOST_DATASETS_FILTER` by roles.
2. Inside each role, scan format directories.
3. For each format, collect all files (`rglob('*')`) and normalize paths to absolute values via `Path.resolve()`.
4. Build structure `ROLE -> FORMAT -> [PATHS]`.
5. Save JSON to `PATH_TEMP_DATA/sort-path-host-file.json`.

Additionally, summary is saved to `PATH_TEMP_DATA/sort-path-host-file-summary.json`.

## Example output JSON (snippet)
```json
{
  "TRAIN": {
    "auth.log": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\host\\TRAIN\\auth.log\\2022-01-13-system.auth.log"
    ],
    "cpu.log": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\host\\TRAIN\\cpu.log\\2022-01-13-system.cpu.log"
    ]
  },
  "TEST": {
    "bson": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\host\\TEST\\bson\\1000.bson"
    ]
  }
}
```

## Execution result
- Created file: `PATH_TEMP_DATA/sort-path-host-file.json`
- Verified grouping by role and format.
- Source data is not modified or deleted.
