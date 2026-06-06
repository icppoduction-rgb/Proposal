# Task46 Report: Analysis of host test json dataset files

## Task Description
Analyzed `PATH_HOST_DATASETS_FILTER\TEST\json` using `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_test_json_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-json-summary.json`
- `docs/ru/analysis-dataset/host/test/json.md`
- `docs/en/analysis-dataset/host/test/json.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task46(Analysis of host test json dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task46(Analysis of host test json dataset files)_report.md`

## JSON Structure
The source `sort-path-host-file.json` is structured as `role -> format -> list[path]`; this task uses `TEST.json`.

## Path Grouping Logic
The handler sorts paths, takes an even sample of up to 30 files, and reads up to 1000 lines / 2097152 bytes per file.

## Result JSON Example
```json
{
  "format": "json",
  "role": "TEST",
  "scope": {
    "total_files_count": 7071,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000,
    "max_bytes_per_file": 2097152
  },
  "schema_kinds": {
    "event_descriptor_json_lines": 1,
    "file_artifact_json_lines": 8,
    "reboot_event_json_lines": 4,
    "multiline_json_document": 8,
    "task_metadata_json": 9
  },
  "final_status": "NEEDS_CUSTOM_PARSER",
  "top_fields": [
    {
      "field": "path",
      "type": "str",
      "observed_count": 1581,
      "example": "shots/0001.jpg"
    },
    {
      "field": "pids",
      "type": "list",
      "observed_count": 1581,
      "example": "[2548]"
    },
    {
      "field": "filepath",
      "type": "str",
      "observed_count": 1059,
      "example": "c:\\docume~1\\nunes\\locals~1\\temp\\tmprywxxi"
    },
    {
      "field": "filepath",
      "type": "NoneType",
      "observed_count": 522,
      "example": "c:\\docume~1\\nunes\\locals~1\\temp\\tmprywxxi"
    },
    {
      "field": "name",
      "type": "unknown",
      "observed_count": 453,
      "example": "__process__"
    }
  ]
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-json-summary.json`. Final status: `NEEDS_CUSTOM_PARSER`.
