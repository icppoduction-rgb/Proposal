# Task2 Report: Analysis of host validation csv dataset files

## Task Description
Analyzed `PATH_HOST_DATASETS_FILTER\VALIDATION\csv` using `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_validation_csv_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-validation-csv-summary.json`
- `docs/ru/analysis-dataset/host/validation/csv.md`
- `docs/en/analysis-dataset/host/validation/csv.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task2(Analysis of host validation csv dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task2(Analysis of host validation csv dataset files)_report.md`

## JSON Structure
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `VALIDATION.csv`.

## Path Grouping Logic
The handler analyzes all CSV files for the format and reads a limited number of rows per file.

## Result JSON Example
```json
{
  "format": "csv",
  "role": "VALIDATION",
  "scope": {
    "total_files_count": 6,
    "sampled_files_count": 6,
    "max_lines_per_file": 1000
  },
  "label_values": {
    "False": 5813,
    "True": 187
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-validation-csv-summary.json`. Final status: `READY_FOR_FEATURE_EXTRACTION`.
