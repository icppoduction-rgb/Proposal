# Merged source inventory

This document records which old files were merged into the new thematic structure. It preserves navigation after duplicate files are removed.

## New documents

| New document | Contents |
| --- | --- |
| [README.md](README.md) | Section map, coverage, readiness counts, invariants. |
| [dns_datasets.md](dns_datasets.md) | All DNS TRAIN/VALIDATION/TEST information. |
| [host_datasets.md](host_datasets.md) | All Host TRAIN/VALIDATION/TEST information. |
| [format_status_matrix.md](format_status_matrix.md) | 64 format buckets: files/status/labels/timestamp/action. |
| [labels_and_readiness.md](labels_and_readiness.md) | Label policy, readiness statuses, LabelResolver guidance. |
| [parser_feature_recommendations.md](parser_feature_recommendations.md) | Parser priorities, feature groups, quality checks. |

## Old top-level files

| Old file | Where its content moved |
| --- | --- |
| `analysis-dataset.md` | `README.md`, `dns_datasets.md`, `host_datasets.md`, `parser_feature_recommendations.md`. |
| `dataset_labels_availability_and_recommendations.md` | `labels_and_readiness.md`, `parser_feature_recommendations.md`. |

## Old split-level aggregates

| Old file | Where its content moved |
| --- | --- |
| `dns/train/general_dns_train.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/validation/general_dns_validation.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/test/general_dns_test.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `host/train/general_host_train.md` | `host_datasets.md`, `format_status_matrix.md`, `parser_feature_recommendations.md`. |
| `host/validation/general_host_validation.md` | `host_datasets.md`, `format_status_matrix.md`. |
| `host/test/general_host_test.md` | `host_datasets.md`, `format_status_matrix.md`. |

## Old per-format files

### DNS

| Old directory | Files | New document |
| --- | --- | --- |
| `dns/train/` | `csv.md`, `pcap.md`, `pcap.csv.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/validation/` | `pcap.md`, `txt.md` | `dns_datasets.md`, `format_status_matrix.md`. |
| `dns/test/` | `csv.md`, `pcap.md`, `pcap.csv.md` | `dns_datasets.md`, `format_status_matrix.md`. |

### Host TRAIN

`host/train/*.md` was merged into `host_datasets.md` and `format_status_matrix.md`.

Format list: `auth.log`, `cpu.log`, `csv`, `diskio.log`, `filesystem.log`, `fsstat.log`, `ghc`, `info`, `journal`, `journal~`, `json`, `json-1`, `load.log`, `log`, `log-1`, `log-2`, `log-3`, `mail-info-1`, `mail-warn-1`, `mainlog`, `mainlog-1`, `mainlog-2`, `mainlog-3`, `memory.log`, `messages`, `messages-1`, `netflow_ids`, `network.log`, `pcap`, `process.log`, `process.summary.log`, `sc`, `service.log`, `socket.summary.log`, `syslog`, `syslog-1`, `syslog-2`, `syslog-3`, `syslog-4`, `syslog.log`, `txt`, `uptime.log`, `xml`.

### Host VALIDATION

`host/validation/*.md` was merged into `host_datasets.md` and `format_status_matrix.md`.

Format list: `cap`, `csv`, `json`, `netflow_day`, `pcap`, `pcapng`, `txt`, `wls_day`.

### Host TEST

`host/test/*.md` was merged into `host_datasets.md` and `format_status_matrix.md`.

Format list: `bson`, `csv`, `json`, `log`, `txt`.

## Why the old files are removed

The old documents contained useful source observations, but they:

- duplicated structure and conclusions in `general_*`;
- made navigation harder across 80 files;
- obscured the overall readiness/label picture;
- partly overlapped with normalization/code documentation.

Their key data has been moved into the new thematic structure.
