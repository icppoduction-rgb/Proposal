# Task47 Report: Analysis of host test log dataset files

## Task Description
Analyzed `PATH_HOST_DATASETS_FILTER\TEST\log` using `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_test_log_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-log-summary.json`
- `docs/ru/analysis-dataset/host/test/log.md`
- `docs/en/analysis-dataset/host/test/log.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task47(Analysis of host test log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task47(Analysis of host test log dataset files)_report.md`

## JSON Structure
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `TEST.log`.

## Path Grouping Logic
The handler sorts paths, takes an even sample of up to 30 files, and reads up to 1000 lines per file.

## Result JSON Example
```json
{
  "format": "log",
  "role": "TEST",
  "scope": {
    "total_files_count": 4086,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_lines": 4834,
  "levels": {
    "DEBUG": 3405,
    "INFO": 1242,
    "WARNING": 171,
    "ERROR": 16
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-log-summary.json`. Final status: `READY_FOR_FEATURE_EXTRACTION`.
