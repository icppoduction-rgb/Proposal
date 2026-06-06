# Task50 Report: Analysis of host test wls_day dataset files

## Task Description
Analyzed `PATH_HOST_DATASETS_FILTER\TEST\wls_day` using `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_test_wls_day_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-wls-day-summary.json`
- `docs/ru/analysis-dataset/host/test/wls_day.md`
- `docs/en/analysis-dataset/host/test/wls_day.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task50(Analysis of host test wls_day dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task50(Analysis of host test wls_day dataset files)_report.md`

## JSON Structure
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `TEST.wls_day`.

## Path Grouping Logic
The handler analyzes all 3 files and reads a limited number of JSON Lines records per file.

## Result JSON Example
```json
{
  "format": "wls_day",
  "role": "TEST",
  "scope": {
    "total_files_count": 3,
    "sampled_files_count": 3,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_records": 3000,
  "event_ids": {
    "4688": 1474,
    "4624": 609,
    "4672": 375,
    "4634": 234,
    "4776": 126,
    "4769": 101,
    "4768": 47,
    "4648": 31,
    "4625": 3
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-wls-day-summary.json`. Final status: `READY_FOR_FEATURE_EXTRACTION`.
