# Task2 Report: Analysis of dns train pcap dataset files

## Task Description
Analyzed `PATH_DNS_DATASETS_FILTER\TRAIN\pcap` using `sort-path-dns-file.json`. Source datasets were not modified, and no model training was performed.

## Added or Changed Files
- `scripts/handlers/analyze_dns_train_pcap_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-dns-train-pcap-summary.json`
- `docs/ru/analysis-dataset/dns/train/pcap.md`
- `docs/en/analysis-dataset/dns/train/pcap.md`
- `docs/ru/analysis-dataset/dns/train/README.md`
- `docs/en/analysis-dataset/dns/train/README.md`
- `report/ru/stage-one/analysis-dataset/dns/train/Task2(Analysis of dns train pcap dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/dns/train/Task2(Analysis of dns train pcap dataset files)_report.md`

## JSON Structure
`sort-path-dns-file.json`: `role -> format -> list[path]`; bucket: `TRAIN.pcap`.

## Analysis Logic
The handler detects classic pcap/pcapng by magic bytes and reads a limited number of packet records.

## Result JSON Example
```json
{
  "format": "pcap",
  "role": "TRAIN",
  "scope": {
    "total_files_count": 4,
    "sampled_files_count": 4,
    "max_files_per_format": 30,
    "max_packets_per_file": 500,
    "max_blocks_per_file": 2000
  },
  "container_variants": {
    "classic_pcap": 3,
    "pcapng": 1
  },
  "parsed_packets": 2000,
  "dns_port_hits_sample": 1000,
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

## Result
Created summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-dns-train-pcap-summary.json`. Final status: `NEEDS_CUSTOM_PARSER`.
