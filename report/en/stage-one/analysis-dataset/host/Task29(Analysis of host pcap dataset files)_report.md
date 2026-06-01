# Report: Task29 (Analysis of host pcap dataset files)

## Task description
Reworked `TRAIN/pcap` content analysis with RU/EN documentation generation and README index updates.

## Added or modified files
- `scripts/handlers/analyze_host_pcap_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/pcap.md`
- `docs/en/analysis-dataset/host/pcap.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task29(Analysis of host pcap dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task29(Analysis of host pcap dataset files)_report.md`
- `temp_data/analysis-host-pcap-summary.json`

## JSON structure summary
- json_document: `0`
- json_lines: `0`
- unparsed: `0`

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket `TRAIN -> pcap`.
3. Apply evenly distributed sampling across all sorted filenames.
4. For each sample file, try `json document` parsing first, then fallback to `json-lines`.

## Sample output JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "pcap",
    "total_files_count": 15,
    "sampled_files_count": 15,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000,
    "max_bytes_per_file": 2097152
  },
  "technical": {
    "schema_counts": {
      "json_document": 0,
      "json_lines": 0,
      "raw_text": 15,
      "unparsed": 0
    }
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-pcap-summary.json`
