# Report: Task10 (Analysis of host journal~ dataset files)

## Task description
Implemented a dedicated analysis stage for `TRAIN/journal~` using `temp_data/sort-path-host-file.json` with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_journal_tilde_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/journal~.md`
- `docs/en/analysis-dataset/host/journal~.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task10(Analysis of host journal~ dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task10(Analysis of host journal~ dataset files)_report.md`
- `temp_data/analysis-host-journal-tilde-summary.json`

## JSON structure description
- binary signature: `LPKSHHRH`
- type: binary container
- suitability status: `NEEDS_CUSTOM_PARSER`

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket: `TRAIN -> journal~`.
3. Read `sort-path-dns-file.json` in parallel for DNS/Host context validation without data mixing.
4. Analyze only bounded samples and safe header bytes.

## Sample of resulting JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "journal~",
    "total_files_count": 1,
    "sampled_files_count": 1,
    "max_files_per_format": 30
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "journal~",
    "dns_formats_detected_count": 3
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

## Result
- Total format files: `1`.
- Sampled files analyzed: `1`.
- Final status: `NEEDS_CUSTOM_PARSER`.

## Artifacts
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-journal-tilde-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\journal~.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\journal~.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
