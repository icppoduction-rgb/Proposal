# Report: Task37 (Analysis of host syslog-2 dataset files)

## Task description
Reworked `TRAIN/syslog-2` content analysis with RU/EN documentation generation and README index updates.

## Added or modified files
- `scripts/handlers/analyze_host_syslog_2_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/syslog-2.md`
- `docs/en/analysis-dataset/host/syslog-2.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task37(Analysis of host syslog-2 dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task37(Analysis of host syslog-2 dataset files)_report.md`
- `temp_data/analysis-host-syslog-2-summary.json`

## JSON structure summary
- json_document: `0`
- json_lines: `0`
- unparsed: `0`

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket `TRAIN -> syslog-2`.
3. Apply evenly distributed sampling across all sorted filenames.
4. For each sample file, try `json document` parsing first, then fallback to `json-lines`.

## Sample output JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "syslog-2",
    "total_files_count": 10,
    "sampled_files_count": 10,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000,
    "max_bytes_per_file": 2097152
  },
  "technical": {
    "schema_counts": {
      "json_document": 0,
      "json_lines": 0,
      "raw_text": 10,
      "unparsed": 0
    }
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-syslog-2-summary.json`
