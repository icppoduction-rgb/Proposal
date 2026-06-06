# Task44 Report: Analysis of host test bson dataset files

## Task Description
Analyzed files under `PATH_HOST_DATASETS_FILTER\TEST\bson` using paths from `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_test_bson_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-bson-summary.json`
- `docs/ru/analysis-dataset/host/test/bson.md`
- `docs/en/analysis-dataset/host/test/bson.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task44(Analysis of host test bson dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task44(Analysis of host test bson dataset files)_report.md`

## JSON Structure
The source `sort-path-host-file.json` is structured as `role -> format -> list[path]`. This task uses the `TEST.bson` bucket.

## Path Grouping Logic
The handler reads only the Host JSON, selects role `TEST` and format `bson`, sorts paths, then takes an evenly distributed sample of up to 30 files. Each file is read with limits of 2097152 bytes and 100 BSON documents.

## Result JSON Example
```json
{
  "format": "bson",
  "role": "TEST",
  "scope": {
    "total_files_count": 9005,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_docs_per_file": 100,
    "max_bytes_per_file": 2097152,
    "total_sampled_bytes": 14878744
  },
  "parsed_document_count": 2325,
  "final_status": "NEEDS_CUSTOM_PARSER",
  "needs_custom_parser": true,
  "top_fields": [
    {
      "field": "I",
      "type": "int32",
      "observed_count": 2325,
      "example": "0"
    },
    {
      "field": "args",
      "type": "array",
      "observed_count": 2325,
      "example": "nested_array"
    },
    {
      "field": "flags_value.information_class.0",
      "type": "array",
      "observed_count": 2091,
      "example": "nested_array"
    },
    {
      "field": "flags_value.information_class.0.0",
      "type": "int32",
      "observed_count": 2091,
      "example": "0"
    },
    {
      "field": "flags_value.information_class.0.1",
      "type": "string",
      "observed_count": 2091,
      "example": "KeyValueBasicInformation"
    }
  ]
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-bson-summary.json`. Final status: `NEEDS_CUSTOM_PARSER`. Dedicated BSON parser required: `true`.
