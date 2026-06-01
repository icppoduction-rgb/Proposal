# Report: Task12 (Analysis of host json-1 dataset files)

## Task description
Reworked `TRAIN/json-1` content analysis with RU/EN documentation generation and README index updates.

## Added or modified files
- `scripts/handlers/analyze_host_json_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/json.md`
- `docs/en/analysis-dataset/host/json.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task12(Analysis of host json-1 dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task12(Analysis of host json-1 dataset files)_report.md`
- `temp_data/analysis-host-json-summary.json`

## JSON structure summary
- json_document: `0`
- json_lines: `1`
- unparsed: `0`

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket `TRAIN -> json`.
3. Apply evenly distributed sampling across all sorted filenames.
4. For each sample file, try `json document` parsing first, then fallback to `json-lines`.

## Sample output JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "json-1",
    "total_files_count": 1,
    "sampled_files_count": 1,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000,
    "max_bytes_per_file": 2097152
  },
  "technical": {
    "schema_counts": {
      "json_document": 0,
      "json_lines": 1,
      "unparsed": 0
    }
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-json-1-summary.json`
