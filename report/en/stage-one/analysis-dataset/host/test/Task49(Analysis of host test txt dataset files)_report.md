# Task49 Report: Analysis of host test txt dataset files

## Task Description
Analyzed `PATH_HOST_DATASETS_FILTER\TEST\txt` using `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_test_txt_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-txt-summary.json`
- `docs/ru/analysis-dataset/host/test/txt.md`
- `docs/en/analysis-dataset/host/test/txt.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task49(Analysis of host test txt dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task49(Analysis of host test txt dataset files)_report.md`

## JSON Structure
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `TEST.txt`.

## Path Grouping Logic
The handler takes an even sample from the large TXT file list and reads a limited number of lines per file.

## Result JSON Example
```json
{
  "format": "txt",
  "role": "TEST",
  "scope": {
    "total_files_count": 274419,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_lines": 6901,
  "top_method_names": {
    "NtSetEventBoostPriority": 1000,
    "ZwAllocateVirtualMemory": 1000,
    "ZwQueryInformationToken": 1000,
    "ZwWaitForSingleObject": 1000,
    "ZwReplyWaitReceivePort": 682
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-txt-summary.json`. Final status: `READY_FOR_FEATURE_EXTRACTION`.
