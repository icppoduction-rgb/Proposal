# Report: export sorted DNS dataset paths to JSON (stage 7)

## Task description
Implemented a handler that exports paths of sorted DNS datasets into JSON.
Source: `PATH_DNS_DATASETS_FILTER`.
Target file: `PATH_TEMP_DATA/sort-path-dns-file.json`.

## Added files
- `scripts/handlers/save_sort_dns_path_handler.py`
- `report/ru/dns_dataset_save_paths_report.md`
- `report/en/dns_dataset_save_paths_report.md`

## Changed files
- `manage.py`

## Run command
- `python manage.py dns dataset save-paths`

Additional alias is supported:
- `python manage.py dataset dns save-paths`

`manage.py` remains an entrypoint only; core logic is implemented in `scripts/handlers/save_sort_dns_path_handler.py`.

## JSON structure
Output JSON structure:

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

- Level 1: dataset role (`TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`).
- Level 2: file format (format directory name).
- Value: list of absolute file paths.

## Path grouping logic
1. Scan `PATH_DNS_DATASETS_FILTER` by roles.
2. Inside each role, scan format directories.
3. Collect all files per format (`rglob('*')`).
4. Normalize paths to absolute values with `Path.resolve()`.
5. Build `ROLE -> FORMAT -> [PATHS]`.
6. Save JSON to `PATH_TEMP_DATA/sort-path-dns-file.json`.

Additional summary is stored in:
- `PATH_TEMP_DATA/sort-path-dns-file-summary.json`.

## Example output JSON (snippet)
```json
{
  "TRAIN": {
    "csv": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\dns\\TRAIN\\csv\\benign_domains.csv"
    ],
    "pcap": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\dns\\TRAIN\\pcap\\benign.pcap"
    ]
  },
  "TEST": {
    "csv": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\dns\\TEST\\csv\\dataset.csv"
    ]
  }
}
```

## Execution result
- Created file: `PATH_TEMP_DATA/sort-path-dns-file.json`
- `scanned_files_count`: `35`
- Grouping by role and format is verified.
- Source DNS data is not modified or deleted.
