# Report: Task6 (Analysis of host fsstat-log dataset files)

## Task description
Implemented a dedicated analysis stage for `TRAIN/fsstat.log` using `temp_data/sort-path-host-file.json` with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_fsstat_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/fsstat.log.md`
- `docs/en/analysis-dataset/host/fsstat.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task6(Analysis of host fsstat-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task6(Analysis of host fsstat-log dataset files)_report.md`
- `temp_data/analysis-host-fsstat-log-summary.json`

## JSON structure description
- top-level keys: metricset, agent, tags, host, @version, system, @timestamp, service, event, ecs
- dataset: `system.fsstat`
- nested fields: `system.fsstat.count/total_files/total_size.used/total_size.free/total_size.total`.

## Path grouping logic
1. Load `sort-path-host-file.json`.
2. Select bucket: `TRAIN -> fsstat.log`.
3. Read `sort-path-dns-file.json` in parallel for DNS/Host context validation without data mixing.
4. Analyze only bounded samples of files and lines.

## Sample of resulting JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "fsstat.log",
    "total_files_count": 12,
    "sampled_files_count": 12,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "fsstat.log",
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
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-fsstat-log-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\fsstat.log.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\fsstat.log.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
