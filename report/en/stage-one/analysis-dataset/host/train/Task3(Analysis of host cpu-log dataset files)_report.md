# Report: Task3 (Analysis of host cpu-log dataset files)

## Task description
Implemented `TRAIN/cpu.log` content analysis using `temp_data/sort-path-host-file.json`, with RU/EN documentation output.

## Added/updated files
- `scripts/handlers/analyze_host_cpu_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/cpu.log.md`
- `docs/en/analysis-dataset/host/cpu.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task3(Analysis of host cpu-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task3(Analysis of host cpu-log dataset files)_report.md`
- `temp_data/analysis-host-cpu-log-summary.json`

## Logic
1. Loaded `TRAIN/cpu.log` paths.
2. Parsed JSON-lines structure and nested CPU metric fields.
3. Checked timestamp, label indicators, and data quality.
4. Detected mixed schemas (metric rows + annotation rows).
5. Generated markdown docs and updated host README.

## Result
- Total format files: `13`.
- Sampled files analyzed: `13`.
- Final status: `PARTIALLY_SUPPORTED`.

## Artifacts
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-cpu-log-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\cpu.log.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\cpu.log.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
