# Task3 Report: Analysis of dns train pcap.csv dataset files

## Task Description
Analyzed `PATH_DNS_DATASETS_FILTER\TRAIN\pcap.csv` using `sort-path-dns-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_dns_train_pcap_csv_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-dns-train-pcap-csv-summary.json`
- `docs/ru/analysis-dataset/dns/train/pcap.csv.md`
- `docs/en/analysis-dataset/dns/train/pcap.csv.md`
- `docs/ru/analysis-dataset/dns/train/README.md`
- `docs/en/analysis-dataset/dns/train/README.md`
- `report/ru/stage-one/analysis-dataset/dns/train/Task3(Analysis of dns train pcap.csv dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/dns/train/Task3(Analysis of dns train pcap.csv dataset files)_report.md`

## JSON Structure
`sort-path-dns-file.json`: `role -> format -> list[path]`; bucket: `TRAIN.pcap.csv`.

## Analysis Logic
The handler reads a limited CSV row sample, detects stateful/stateless schemas, collects column types, label hints from file names, and data-quality signals.

## Result JSON Example
```json
{
  "format": "pcap.csv",
  "role": "TRAIN",
  "scope": {
    "total_files_count": 14,
    "sampled_files_count": 14,
    "max_files_per_format": 30,
    "max_rows_per_file": 1000
  },
  "schema_kinds": {
    "stateful_dns_pcap_features": 7,
    "stateless_dns_pcap_features": 7
  },
  "class_hints": {
    "audio": 2,
    "benign": 2,
    "compressed": 2,
    "exe": 2,
    "image": 2,
    "text": 2,
    "video": 2
  },
  "parsed_rows": 12577,
  "timestamp_columns": [
    "timestamp"
  ],
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-dns-train-pcap-csv-summary.json`. Final status: `READY_FOR_FEATURE_EXTRACTION`.
