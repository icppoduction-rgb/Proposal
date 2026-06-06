# Task45 Report: Analysis of host test csv dataset files

## Task Description
Analyzed files under `PATH_HOST_DATASETS_FILTER\TEST\csv` using paths from `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_test_csv_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-csv-summary.json`
- `docs/ru/analysis-dataset/host/test/csv.md`
- `docs/en/analysis-dataset/host/test/csv.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task45(Analysis of host test csv dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task45(Analysis of host test csv dataset files)_report.md`

## JSON Structure
The source `sort-path-host-file.json` is structured as `role -> format -> list[path]`. This task uses the `TEST.csv` bucket.

## Path Grouping Logic
The handler reads the Host JSON, selects role `TEST` and format `csv`, sorts paths, and analyzes up to 30 files. For each CSV, up to 1000 rows are read.

## Result JSON Example
```json
{
  "format": "csv",
  "role": "TEST",
  "scope": {
    "total_files_count": 3,
    "sampled_files_count": 3,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "final_status": "PARTIALLY_SUPPORTED",
  "label_values": {
    "nmap_tcp_syn": 2,
    "nmap_tcp_conn": 2,
    "nmap_tcp_null": 2,
    "nmap_tcp_xmas": 2,
    "nmap_tcp_fin": 2,
    "nmap_tcp_ack": 2,
    "nmap_tcp_window": 2,
    "nmap_tcp_maimon": 2,
    "unicornscan_tcp_syn": 2,
    "unicornscan_tcp_conn": 2,
    "unicornscan_tcp_null": 2,
    "unicornscan_tcp_xmas": 2,
    "unicornscan_tcp_fxmas": 2,
    "unicornscan_tcp_fin": 2,
    "unicornscan_tcp_ack": 2,
    "hping_tcp_syn": 2,
    "hping_tcp_null": 2,
    "hping_tcp_xmas": 2,
    "hping_tcp_fin": 2,
    "hping_tcp_ack": 2,
    "zmap_tcp_syn": 2,
    "masscan_tcp_syn": 2,
    "nmap_ping_scan": 1,
    "nmap_vvv": 1,
    "nmap_connect": 1,
    "nmap_fast": 1,
    "nmap_servinfo": 1,
    "nmap_reason": 1,
    "nmap_open": 1,
    "nmap_top10": 1
  },
  "fields": [
    {
      "field": "ip",
      "type": "ip",
      "observed_files": 2,
      "example": "172.16.0.3"
    },
    {
      "field": "label",
      "type": "string",
      "observed_files": 2,
      "example": "nmap_tcp_syn"
    },
    {
      "field": "frame_info.encap_type",
      "type": "integer",
      "observed_files": 1,
      "example": "1"
    },
    {
      "field": "frame_info.time",
      "type": "string",
      "observed_files": 1,
      "example": "Dec 31, 1969 21:03:41.953641000 -03"
    },
    {
      "field": "frame_info.time_epoch",
      "type": "float",
      "observed_files": 1,
      "example": "221.953641000"
    }
  ]
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-csv-summary.json`. Final status: `PARTIALLY_SUPPORTED`.
