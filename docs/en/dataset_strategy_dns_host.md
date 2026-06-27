# DNS and Host dataset strategy

This document merges `dns_dataset_strategy.md`, `host_datasets_analysis.md`, dataset role sections from `functional_project_cheatsheet.md`, and dataset mappings from `dataset_feature_extraction_map.md`. DNS and Host logic are separated explicitly; `TRAIN`, `VALIDATION`, and `TEST` are not mixed.

## General rules

- `TRAIN` is used for training and fit preprocessing.
- `VALIDATION` is used for tuning, false-positive control, and robustness checks.
- `TEST` is used only for final evaluation/inference.
- DNS and Host are not joined at raw level.
- Hybrid integration happens through normalized events, windows, feature artifacts, and traceability.
- Experimental datasets are not promoted to `TRAIN` without a separate decision.

## DNS strategy

| Role | Dataset | Purpose | Source |
| --- | --- | --- | --- |
| `TRAIN` | CIC-Bell-DNS-EXF-2021 | Attack-class behaviour: DNS exfiltration/tunneling. | <https://www.unb.ca/cic/datasets/dns-exf-2021.html> |
| `TRAIN` | CIC-Bell-DNS-2021 | Benign baseline and normal DNS behaviour. | <https://www.unb.ca/cic/datasets/dns-2021.html> |
| `VALIDATION` | Split CIC-Bell-DNS-2021 | False-positive control and threshold tuning. | <https://www.unb.ca/cic/datasets/dns-2021.html> |
| `TEST` | Mendeley DNS Exfiltration Dataset | Independent generalization and transferability check. | <https://data.mendeley.com/datasets/c4n7fckkz3/3> |

```text
DNS TRAIN:
  - CIC-Bell-DNS-EXF-2021
  - CIC-Bell-DNS-2021

DNS VALIDATION:
  - split CIC-Bell-DNS-2021

DNS TEST:
  - Mendeley DNS Exfiltration Dataset
```

## Host strategy

| Role | Dataset | Purpose | Source |
| --- | --- | --- | --- |
| `TRAIN` | ADFA IDS | Baseline HIDS training, normal/attack host traces, syscall sequences. | <https://research.unsw.edu.au/projects/adfa-ids-datasets>; <https://www.kaggle.com/datasets/alishamekhi/adfa-ids-datasets?resource=download> |
| `TRAIN` | LID-DS 2021 | Core sequence modelling dataset for Linux syscall behaviour. | <https://github.com/LID-DS/LID-DS> |
| `TRAIN` | Maintainable Log Dataset | Enterprise log behaviour and multi-stage attack modelling. | <https://data.niaid.nih.gov/resources?id=zenodo_5789063> |
| `VALIDATION` | LID-DS 2019 | Cross-version validation on CVE-based attack scenarios. | <https://github.com/LID-DS/LID-DS> |
| `VALIDATION` | LANL Dataset | User-host behaviour, authentication behaviour, lateral movement patterns. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| `VALIDATION` | Windows Event Log / OTRF Security Datasets | SOC-style validation on Windows/Sysmon telemetry. | <https://github.com/OTRF/Security-Datasets> |
| `TEST` | Unified Host + Network Dataset / LANL | Hybrid host+network validation, multi-source telemetry, feature-level fusion. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| `TEST` | ISOT Cloud IDS Dataset | Cloud environment validation, workloads, logs/syscalls/performance metrics. | <https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php> |
| `TEST` | Dynamic Malware Analysis Dataset | Malware-driven host behaviour and exfiltration-related activity. | <https://zenodo.org/record/1203289> |

## Host dataset details

| Dataset | Role | Contents | Why it is needed | Suitable models | Source |
| --- | --- | --- | --- | --- | --- |
| ADFA IDS | `TRAIN` | Linux/Windows system calls, normal traces, attack traces. | Standard HIDS baseline and research comparability. | RF, XGBoost, LSTM, CNN. | <https://research.unsw.edu.au/projects/adfa-ids-datasets>; <https://www.kaggle.com/datasets/alishamekhi/adfa-ids-datasets?resource=download> |
| LID-DS 2021 | `TRAIN` | System calls, attack scenarios, normal behaviour, labelled traces. | Main source for the LSTM/sequence branch. | LSTM, GRU, CNN-LSTM, Transformers. | <https://github.com/LID-DS/LID-DS> |
| Maintainable Log Dataset | `TRAIN` | Enterprise logs, 20 log types, multi-stage attacks via state machines. | Validates log-level multi-stage behaviour, not only syscalls. | RF, XGBoost, LSTM/GRU, Autoencoder. | <https://data.niaid.nih.gov/resources?id=zenodo_5789063> |
| LID-DS 2019 | `VALIDATION` | CVE-based scenarios, syscall parameters, labelled attacks, benign traces. | Tests transfer from LID-DS 2021 to 2019. | Same syscall/sequence models. | <https://github.com/LID-DS/LID-DS> |
| LANL Dataset | `VALIDATION` | Authentication logs, user-computer events, multi-day enterprise activity. | Covers user/auth/lateral movement behaviour. | Graph/sequence/tabular auth models. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| Windows Event Log / OTRF | `VALIDATION` | Windows Event Logs, Sysmon, process/security events. | SOC-oriented validation and Windows telemetry. | RF, XGBoost, sequence/event models. | <https://github.com/OTRF/Security-Datasets> |
| Unified Host + Network / LANL | `TEST` | Host events, network events, authentication activity. | Final hybrid host+network fusion check. | Hybrid/late-fusion models. | <https://github.com/trenton3983/Cybersecurity-Datasets> |
| ISOT Cloud IDS | `TEST` | Cloud logs, syscalls, performance metrics. | Cloud-like portability check. | Resource/log/sequence models. | <https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php> |
| Dynamic Malware Analysis | `TEST` | Kernel calls, user-level activity, malware traces. | Malware-driven host behaviour check. | API/syscall/process models. | <https://zenodo.org/record/1203289> |

## Experiments only

| Dataset | Status | Limitation |
| --- | --- | --- |
| HDFS Log Dataset / LogHub | Experiments only | Not security-focused; use only for log anomaly pipeline checks. |
| Synthetic syscall augmentation / extra syscall traces | Experiments only | Do not use as the main ground-truth source without a separate methodology. |

## Attack lifecycle coverage

| Stage | Supporting sources |
| --- | --- |
| Reconnaissance | OTRF, Maintainable Log Dataset, Unified Host-Network. |
| Privilege Escalation | OTRF, LANL, Unified Host-Network. |
| Lateral Movement | LANL, OTRF, Unified Host-Network. |
| Collection | ADFA IDS, LID-DS 2021/2019, Dynamic Malware Analysis, Maintainable Log Dataset, Unified Host-Network. |
| Data Staging | ADFA IDS, LID-DS 2021/2019, Maintainable Log Dataset, Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network. |
| Exfiltration | CIC-Bell-DNS-EXF-2021, CIC-Bell-DNS-2021, Mendeley DNS, Unified Host-Network. |

## Final scheme

```text
DNS branch:
  TRAIN -> CIC-Bell-DNS-EXF-2021 + CIC-Bell-DNS-2021
  VALIDATION -> split CIC-Bell-DNS-2021
  TEST -> Mendeley DNS Exfiltration Dataset

Host branch:
  TRAIN -> ADFA IDS + LID-DS 2021 + Maintainable Log Dataset
  VALIDATION -> LID-DS 2019 + LANL + Windows Event Logs / OTRF
  TEST -> Unified Host + Network / LANL + ISOT Cloud IDS + Dynamic Malware Analysis
```

Hybrid learning is built on feature-level fusion and late fusion. Raw logs, syscalls, packet captures, and auth events are not mechanically merged into one dataset.
