# Dataset → Feature Extraction Map (Updated)

This document maps each dataset to the specific features to extract for model training, validation, and testing. The mapping is designed to provide coverage across the full data exfiltration lifecycle:

1. Reconnaissance
2. Privilege Escalation
3. Lateral Movement
4. Collection
5. Data Staging
6. Exfiltration

---

# Data Exfiltration Lifecycle Coverage

| Stage | Supporting Datasets |
|---|---|
| Reconnaissance | OTRF, Maintainable Log Dataset, Unified Host-Network |
| Privilege Escalation | OTRF, LANL, Unified Host-Network |
| Lateral Movement | LANL, OTRF, Unified Host-Network |
| Collection | ADFA IDS, LID-DS 2021, LID-DS 2019, Dynamic Malware Analysis, Maintainable Log Dataset, Unified Host-Network |
| Data Staging | ADFA IDS, LID-DS 2021, LID-DS 2019, Maintainable Log Dataset, Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network |
| Exfiltration | CIC-Bell-DNS-EXF-2021, CIC-Bell-DNS-2021, Mendeley DNS Dataset, Unified Host-Network |

---

# DNS Branch

## CIC-Bell-DNS-EXF-2021
- Role: Train
- Attack Stage: Exfiltration

| Category | Features |
|---|---|
| Statistical | Query length, subdomain length, unique subdomain count, unique-to-total subdomain ratio |
| Entropy | Shannon entropy, query string entropy |
| Temporal | Query rate, inter-query timing, queries per time window |
| Protocol | Response size, TTL distributions, query type distribution |
| Dataset-specific | Stateful and stateless DNS features |

## CIC-Bell-DNS-2021
- Role: Train + Validation
- Attack Stage: Exfiltration

| Category | Features |
|---|---|
| Features | Same feature set as EXF-2021 |
| Purpose | Benign baseline and false-positive calibration |

## Mendeley DNS Exfiltration Dataset
- Role: Test
- Attack Stage: Exfiltration

| Category | Features |
|---|---|
| Features | Same feature set as EXF-2021 |
| Purpose | Cross-dataset generalisation testing |

---

# Host Branch — System Call Datasets

## ADFA IDS
- Role: Train
- Attack Stage: Collection, Data Staging

| Category | Features |
|---|---|
| Frequency | Syscall frequency distributions |
| N-grams | Bigram and trigram frequencies |
| Transitions | Syscall transition probabilities |
| Complexity | Unique syscall count, trace length |
| Collection Indicators | open(), read(), access(), stat(), readdir() frequencies |
| Collection Indicators | File enumeration, directory traversal behaviour |
| Sequence | Raw syscall sequences for LSTM |

## LID-DS 2021
- Role: Train
- Attack Stage: Collection, Data Staging, Exfiltration Preparation

| Category | Features |
|---|---|
| Syscall Features | Same as ADFA IDS |
| Parameters | Syscall argument values |
| Temporal | Inter-syscall timing intervals |
| Collection | File access frequency, file enumeration |
| Behavioural | Suspicious process execution chains |

## LID-DS 2019
- Role: Validation
- Attack Stage: Collection, Data Staging

| Category | Features |
|---|---|
| Features | Same feature set as LID-DS 2021 |
| Purpose | Cross-version validation |

---

# Host Branch — Authentication and Enterprise Logs

## LANL Dataset
- Role: Validation
- Attack Stage: Privilege Escalation, Lateral Movement

| Category | Features |
|---|---|
| Auth Patterns | Host pair frequency, auth success/failure ratio |
| Temporal | Login distributions, session duration |
| Behavioural | User-host interaction frequency |
| Privilege Escalation | Admin login ratio, privileged account usage |
| Authentication | Failed login count, unusual account usage |
| Anomaly | Deviation from baseline behaviour |

## Windows Event Log / OTRF Security Datasets
- Role: Validation
- Attack Stage: Reconnaissance, Privilege Escalation, Lateral Movement

| Category | Features |
|---|---|
| Event IDs | 4624, 4625, 4672, Sysmon Event 1 |
| Process Chains | Parent-child process relationships |
| Privilege Indicators | Elevated process execution |
| PowerShell | Encoded command execution |
| Discovery | Account and system discovery events |
| Command-line | Argument entropy |
| Temporal | Event rate and event sequences |

## Maintainable Log Dataset
- Role: Train
- Attack Stage: Reconnaissance, Collection, Data Staging

| Category | Features |
|---|---|
| Log Patterns | Event sequence patterns |
| Volume | Log volume spikes |
| Collection | File-related event frequency |
| Multi-stage | Cross-log correlations |
| Temporal | Event rate and inter-event timing |

---

# Host Branch — Test Datasets

## Dynamic Malware Analysis Dataset
- Role: Test
- Attack Stage: Collection, Data Staging, Exfiltration Preparation

| Category | Features |
|---|---|
| Kernel Calls | Kernel call distributions |
| Collection | File access and discovery activity |
| Process Behaviour | Malware process spawning |
| User Activity | User-level behaviour patterns |

## ISOT Cloud IDS Dataset
- Role: Test
- Attack Stage: Data Staging

| Category | Features |
|---|---|
| Syscalls | Same syscall features as ADFA/LID-DS |
| Cloud Metrics | CPU, memory, I/O anomalies |
| Logs | Cloud workload log patterns |

## Unified Host-Network Dataset (LANL)
- Role: Test
- Attack Stage: Reconnaissance, Privilege Escalation, Lateral Movement, Collection, Data Staging, Exfiltration

| Category | Features |
|---|---|
| Host | Authentication logs, process events |
| Privilege Escalation | Privilege-related host features |
| Collection | File access features |
| Network | Flow duration, bytes, packets, protocol, connection state |
| Fusion | Host-network correlated features |
| Purpose | End-to-end validation of multi-source architecture |

---

# Experiments Only

## HDFS Log Dataset
- Role: Experiments
- Attack Stage: N/A

| Category | Features |
|---|---|
| Features | Structured log sequences, anomaly labels |
| Purpose | Log parsing pipeline validation only |
