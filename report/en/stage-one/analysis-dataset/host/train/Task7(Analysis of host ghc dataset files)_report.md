# Report: Task7 (Analysis of host ghc dataset files)

## Task description
Implemented a dedicated analysis stage for `TRAIN/ghc` using `temp_data/sort-path-host-file.json` with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_ghc_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/ghc.md`
- `docs/en/analysis-dataset/host/ghc.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task7(Analysis of host ghc dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task7(Analysis of host ghc dataset files)_report.md`
- `temp_data/analysis-host-ghc-summary.json`

## JSON structure description
- trace format: `<module>+0x<offset>`
- type: text sequences
- suitability status: `NEEDS_CUSTOM_PARSER`

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket: `TRAIN -> ghc`.
3. Read `sort-path-dns-file.json` in parallel for DNS/Host context validation without data mixing.
4. Analyze only bounded samples of files and lines.

## Sample of resulting JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "ghc",
    "total_files_count": 56158,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "ghc",
    "dns_formats_detected_count": 3
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

## Result
- Total format files: `56158`.
- Sampled files analyzed: `30`.
- Final status: `NEEDS_CUSTOM_PARSER`.

## Artifacts
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-ghc-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\ghc.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\ghc.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
