# Dataset → Feature Extraction Map

This document maps each dataset to the specific features to extract for model training, validation, and testing.

---

## DNS Branch

### CIC-Bell-DNS-EXF-2021

- **Role:** Train
- **Attack stage:** Exfiltration

| Category | Features |
|---|---|
| Statistical | Query length, subdomain length, unique subdomain count, unique-to-total subdomain ratio |
| Entropy | Shannon entropy of domain characters, query string entropy |
| Temporal | Query rate per domain, inter-query timing intervals, queries per time window (LSTM input) |
| Protocol | Response size, TTL distributions, query type distribution (TXT/MX/CNAME) |
| Dataset-specific | Stateful features (connection-level), stateless features (per-query) |

---

### CIC-Bell-DNS-2021

- **Role:** Train + Validation
- **Attack stage:** Exfiltration

| Category | Features |
|---|---|
| Features | Same feature set as EXF-2021 — applied to benign class (~99% benign) |
| Purpose | Normal DNS traffic baseline, false positive calibration, benign class balancing |

---

### Mendeley DNS Exfiltration Dataset

- **Role:** Test
- **Attack stage:** Exfiltration

| Category | Features |
|---|---|
| Features | Same feature set as EXF-2021 — applied to independent exfiltration data |
| Purpose | Cross-dataset generalisation, real-world pattern robustness check |

---

## Host Branch — System Call Datasets

### ADFA IDS

- **Role:** Train
- **Attack stage:** Data staging / Collection

| Category | Features |
|---|---|
| Frequency | Syscall frequency distribution per trace (count of each unique syscall ID) |
| N-grams | Bigram and trigram frequencies of syscall sequences |
| Transitions | Syscall-to-syscall transition probabilities (LSTM input) |
| Complexity | Unique syscall count per trace, trace length |
| Sequence | Raw ordered syscall IDs (direct LSTM sequence input) |

---

### LID-DS 2021

- **Role:** Train
- **Attack stage:** Data staging / Collection

| Category | Features |
|---|---|
| Syscall features | Same as ADFA IDS |
| Parameters | Syscall argument values (if available) |
| Temporal | Inter-syscall timing intervals, syscall rate per time window |
| Purpose | Primary dataset for LSTM sequence modelling of process behaviour |

---

### LID-DS 2019

- **Role:** Validation
- **Attack stage:** Data staging / Collection

| Category | Features |
|---|---|
| Features | Same feature set as LID-DS 2021 |
| Purpose | Cross-version validation, CVE-based attack scenarios, overfitting check |

---

## Host Branch — Authentication and Enterprise Logs

### LANL Dataset

- **Role:** Validation
- **Attack stage:** Lateral movement / Privilege escalation

| Category | Features |
|---|---|
| Auth patterns | Source-destination host pair frequency, auth success/failure ratio per user |
| Temporal | Time-of-day and day-of-week login distributions, session duration |
| Behavioural | User-host interaction frequency, new host-pair connections |
| Anomaly | Deviation from user baseline access patterns |

---

### Windows Event Log / OTRF Security Datasets

- **Role:** Validation
- **Attack stage:** Reconnaissance, Lateral movement

| Category | Features |
|---|---|
| Event IDs | Frequency of 4624/4625 (logon), 4672 (privilege), Sysmon Event 1 (process creation) |
| Process chains | Parent-child process tree depth, unusual parent-child pairs |
| Command-line | Argument string entropy (obfuscation detection) |
| Temporal | Event rate per host, event sequence patterns |

---

### Maintainable Log Dataset

- **Role:** Train
- **Attack stage:** Reconnaissance, Data staging

| Category | Features |
|---|---|
| Log patterns | Event sequence patterns across 20 log types |
| Volume | Log volume per host over time (spike detection) |
| Multi-stage | Cross-log-type event correlations for attack progression |
| Temporal | Log event rate, inter-event timing (LSTM sequence input) |

---

## Host Branch — Test Datasets

### Dynamic Malware Analysis Dataset

- **Role:** Test
- **Attack stage:** Data staging, Exfiltration

| Category | Features |
|---|---|
| Kernel calls | Kernel call frequency distributions |
| User activity | User-level activity patterns during malware execution |
| Purpose | Malware-driven behaviour, pre-exfiltration host activity |

---

### ISOT Cloud IDS Dataset

- **Role:** Test
- **Attack stage:** Data staging

| Category | Features |
|---|---|
| Syscalls | Same syscall features as ADFA/LID-DS (if available) |
| Cloud metrics | CPU/memory/IO performance anomalies |
| Logs | System log patterns in cloud workloads |
| Purpose | Cloud environment transferability check |

---

### Unified Host-Network Dataset (LANL)

- **Role:** Test
- **Attack stage:** Reconnaissance, Lateral movement, Data staging, Exfiltration

| Category | Features |
|---|---|
| Host | Auth logs, process events (same features as LANL) |
| Network | Flow duration, bytes, packets, protocol, connection state |
| Fusion | Paired host+network features from same environment |
| Purpose | Validates multi-source integration architecture against genuinely paired data |

---
