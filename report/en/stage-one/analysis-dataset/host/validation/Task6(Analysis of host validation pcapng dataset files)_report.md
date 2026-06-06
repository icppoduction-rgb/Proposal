# Task6 Report: Analysis of host validation pcapng dataset files

## Task Description
Analyzed `PATH_HOST_DATASETS_FILTER\VALIDATION\pcapng` using `sort-path-host-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_host_validation_pcapng_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-validation-pcapng-summary.json`
- `docs/ru/analysis-dataset/host/validation/pcapng.md`
- `docs/en/analysis-dataset/host/validation/pcapng.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task6(Analysis of host validation pcapng dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task6(Analysis of host validation pcapng dataset files)_report.md`

## JSON Structure
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `VALIDATION.pcapng`.

## Analysis Logic
The handler reads pcapng Section Header, Interface Description, and a limited number of Enhanced Packet blocks.

## Result JSON Example
```json
{
  "format": "pcapng",
  "role": "VALIDATION",
  "scope": {
    "total_files_count": 5,
    "sampled_files_count": 5,
    "max_files_per_format": 30,
    "max_blocks_per_file": 2000,
    "max_packets_per_file": 500
  },
  "parsed_packets": 1664,
  "block_types": {
    "0x00000006": 1664,
    "0x0a0d0d0a": 5,
    "0x00000001": 5,
    "0x00000005": 2
  },
  "ip_protocols": {
    "6": 1353,
    "17": 56,
    "1": 40,
    "2": 16
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-validation-pcapng-summary.json`. Final status: `NEEDS_CUSTOM_PARSER`.
