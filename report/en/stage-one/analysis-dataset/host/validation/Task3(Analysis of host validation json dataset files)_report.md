# Task3 Report: Analysis of host validation json dataset files

## Task Description
Analyzed `PATH_HOST_DATASETS_FILTER\VALIDATION\json` using `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_validation_json_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-validation-json-summary.json`
- `docs/ru/analysis-dataset/host/validation/json.md`
- `docs/en/analysis-dataset/host/validation/json.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task3(Analysis of host validation json dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task3(Analysis of host validation json dataset files)_report.md`

## JSON Structure
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `VALIDATION.json`.

## Path Grouping Logic
The handler takes an even sample of JSON files and reads a limited number of JSON Lines records per file.

## Result JSON Example
```json
{
  "format": "json",
  "role": "VALIDATION",
  "scope": {
    "total_files_count": 130,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_records": 19930,
  "event_ids": {
    "10": 5590,
    "7": 2793,
    "12": 2404,
    "13": 1055,
    "4658": 989,
    "5156": 867,
    "800": 609,
    "4103": 553,
    "4656": 531,
    "5158": 510,
    "4690": 469,
    "5447": 436,
    "4663": 353,
    "23": 320,
    "4703": 278,
    "4799": 195,
    "3": 191,
    "9": 178,
    "11": 140,
    "4673": 135
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-validation-json-summary.json`. Final status: `READY_FOR_FEATURE_EXTRACTION`.
