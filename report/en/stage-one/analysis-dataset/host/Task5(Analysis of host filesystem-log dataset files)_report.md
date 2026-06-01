# Report: Task5 (Analysis of host filesystem-log dataset files)

## Task description
Implemented a dedicated analysis stage for `TRAIN/filesystem.log` using `temp_data/sort-path-host-file.json` with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_filesystem_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/filesystem.log.md`
- `docs/en/analysis-dataset/host/filesystem.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task5(Analysis of host filesystem-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task5(Analysis of host filesystem-log dataset files)_report.md`
- `temp_data/analysis-host-filesystem-log-summary.json`

## JSON structure description
- top-level keys: ecs, agent, tags, host, @version, system, @timestamp, service, event, metricset
- dataset: `system.filesystem`
- nested fields: `system.filesystem.mount_point/type/device_name/used/total/free/available`.

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket: `TRAIN -> filesystem.log`.
3. Read `sort-path-dns-file.json` in parallel for DNS/Host context validation without data mixing.
4. Analyze only bounded samples of files and lines.

## Sample of resulting JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "filesystem.log",
    "total_files_count": 12,
    "sampled_files_count": 12,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "filesystem.log",
    "dns_formats_detected_count": 3
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Result
- Total format files: `12`.
- Sampled files analyzed: `12`.
- Final status: `READY_FOR_FEATURE_EXTRACTION`.

## Artifacts
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-filesystem-log-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\filesystem.log.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\filesystem.log.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
