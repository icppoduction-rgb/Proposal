# Host Dataset Strategy for Host-Based Intrusion Detection and Hybrid IDS

## 1. Purpose of the Document

This document defines the set of datasets for training, validation, testing, and experiments in the host-side part of the project for detecting intrusions, malicious behavior, user anomalies, and hybrid host + network activity.

The main goal is to avoid mixing dataset roles and to use each dataset for its intended purpose:

- **TRAIN**: train the model on normal and attack host traces, syscall sequences, and enterprise logs.
- **VALIDATION**: evaluate robustness on other data generations, user-host behavior, and SOC telemetry.
- **TEST**: perform the final generalization check on hybrid, cloud, and malware-driven data.
- **EXPERIMENTS**: run quick experiments, log anomaly detection, synthetic augmentation, and search for additional sources.

---

# 2. Required Datasets

## 1. ADFA IDS

### Role

**Primary baseline dataset for Host Intrusion Detection Systems.**

### Links

<https://research.unsw.edu.au/projects/adfa-ids-datasets>

<https://www.kaggle.com/datasets/alishamekhi/adfa-ids-datasets?resource=download>

### Fact

ADFA IDS is a classic benchmark for Host Intrusion Detection Systems.

### Contents

- Linux system calls;
- Windows system calls;
- normal traces;
- attack traces.

### Why It Is Needed

It is used as a **baseline HIDS training dataset** for initial model evaluation and comparison with existing research approaches.

Main tasks:

- baseline normal and attack host traces;
- initial model validation;
- comparability with classic HIDS approaches;
- training on system call sequences.

### Suitable Models

| Model Type | Application |
|---|---|
| Random Forest | baseline ML model |
| XGBoost | strong baseline for tabular features |
| LSTM | sequence modelling over system call sequences |
| CNN | analysis of local patterns in syscall sequences |

### Why It Is Critical

ADFA is one of the standard datasets for HIDS. Without it, it is difficult to justify the baseline and compare the project with existing research approaches.

### Use in the Project

```text
TRAIN:
- baseline HIDS training
- normal host traces
- attack host traces
- system call sequences
```

---

## 2. LID-DS 2021

### Role

**Primary sequence dataset for host-based detection.**

### Link

<https://github.com/LID-DS/LID-DS>

### Fact

LID-DS 2021 is a modern dataset for Linux-based intrusion detection based on system calls and attack scenarios.

### Contents

- system calls;
- attack scenarios;
- normal behavior;
- labelled traces.

### Why It Is Needed

It is used as a **core sequence modelling dataset** for training models that analyze process behavior over time.

Main tasks:

- syscall sequence modelling;
- training LSTM, GRU, and CNN-LSTM models;
- analysis of temporal patterns in host behavior;
- training on normal and attack traces.

### Suitable Models

| Model Type | Application |
|---|---|
| LSTM | analysis of system call sequences |
| GRU | lighter sequence modelling |
| CNN-LSTM | local syscall patterns plus temporal dynamics |
| Transformer-based models | modelling long-range dependencies in syscall sequences |

### Why It Is Critical

LID-DS 2021 is better suited for modelling behavior over time than simple tabular host logs. It is the key dataset for the LSTM part of the project.

### Use in the Project

```text
TRAIN:
- syscall sequence modelling
- Linux host behavior
- attack scenarios
- labelled traces
```

---

## 3. Maintainable Log Dataset

### Role

**Primary dataset for enterprise log behavior and multi-stage attack modelling.**

### Link

<https://data.niaid.nih.gov/resources?id=zenodo_5789063>

### Fact

The Maintainable Log Dataset contains enterprise logs and multi-stage attacks modelled through state machines.

### Contents

- system logs;
- enterprise logs;
- 20 log types;
- multi-stage attack behavior.

### Why It Is Needed

It is used to evaluate behavioral modelling and detection of multi-stage attacks in log-level telemetry.

Main tasks:

- anomaly detection;
- user and host behavior modelling;
- temporal pattern detection;
- feature-level fusion;
- validation of multi-stage attack behavior.

### Suitable Models

| Model Type | Application |
|---|---|
| Random Forest | baseline over aggregated log features |
| XGBoost | strong baseline for feature-level fusion |
| LSTM / GRU | temporal pattern detection |
| Autoencoder | anomaly detection over log behavior |

### Why It Is Critical

System calls show low-level process behavior, but they do not always capture the full picture of an enterprise attack. The Maintainable Log Dataset is needed to demonstrate that the project works not only at syscall level, but also at log-level behavior.

### Use in the Project

```text
TRAIN:
- enterprise log behavior modelling
- multi-stage attack behavior
- temporal log patterns
- feature-level fusion
```

---

# 3. Additional Datasets

## 4. LID-DS 2019

### Role

**Validation dataset for CVE-based attacks and cross-version evaluation.**

### Link

<https://fkie-cad.github.io/COMIDDS/content/datasets/lids_ds_2019/>

### Fact

LID-DS 2019 contains CVE-based attack scenarios with system calls and syscall parameters.

### Contents

- system calls;
- syscall parameters;
- labelled attacks;
- benign traces.

### Why It Is Needed

It is used for validation and robustness evaluation on another generation of LID-DS data.

Main scenario:

```text
TRAIN:
- LID-DS 2021

VALIDATION:
- LID-DS 2019
```

### It Checks

- whether the model transfers between LID-DS 2021 and LID-DS 2019;
- whether the model overfits to specific attack traces;
- how well syscall-level features work;
- robustness against CVE-based attack scenarios.

### Why It Is Important

LID-DS 2019 provides cross-dataset validation inside the same family of host-based datasets. This helps separate real model quality from overfitting to specific traces.

### Use in the Project

```text
VALIDATION:
- cross-version validation
- CVE-based attack scenarios
- syscall parameters
- benign traces
```

---

## 5. LANL Dataset

### Role

**Evaluation of enterprise authentication behavior and user-host anomalies.**

### Link

<https://github.com/trenton3983/Cybersecurity-Datasets>

### Fact

The Los Alamos National Laboratory dataset contains enterprise authentication logs and user-computer events.

### Contents

- authentication logs;
- user-computer events;
- multi-day activity;
- enterprise behavior.

### Why It Is Needed

It is used to model user and host behavior in a corporate environment.

### It Checks

- lateral movement patterns;
- abnormal login behavior;
- user-host interaction anomalies;
- long-term behavioral deviations.

### Why It Is Important

LANL covers a weak point of syscall datasets: they describe processes well, but they describe user and infrastructure behavior poorly.

### Use in the Project

```text
VALIDATION:
- user-host behavior
- authentication behavior
- lateral movement patterns
- long-term behavioral deviations
```

---

## 6. Windows Event Log / OTRF Security Datasets

### Role

**SOC-level validation on Windows host telemetry.**

### Link

<https://github.com/OTRF/Security-Datasets>

### Fact

OTRF Security Datasets contain Windows security logs, often including Sysmon-based telemetry.

### Contents

- Windows Event Logs;
- Sysmon events;
- process activity;
- security events.

### Why It Is Needed

It is used to evaluate the model on real SOC-style data and Windows host behavior.

### It Checks

- Windows host behavior;
- process creation events;
- suspicious parent-child process chains;
- event-based anomaly detection;
- applicability to SOC telemetry.

### Why It Is Important

ADFA and LID-DS are more focused on syscall-level detection. Windows Event Logs add SOC practicality and connect research to real security operations.

### Use in the Project

```text
VALIDATION:
- SOC-style validation
- Windows host behavior
- Sysmon telemetry
- event-based anomaly detection
```

---

## 7. Unified Host + Network Dataset / LANL

### Role

**Hybrid validation for host + network detection.**

### Link

<https://github.com/trenton3983/Cybersecurity-Datasets>

### Fact

Unified Host + Network Dataset / LANL is a rare dataset that combines host logs and network-level data.

### Contents

- host events;
- network events;
- authentication activity;
- multi-source telemetry.

### Why It Is Needed

It is used to evaluate the hybrid approach and feature-level fusion between host telemetry and network telemetry.

### It Checks

- whether host-level features improve network-level detection;
- whether host telemetry and network telemetry can be combined;
- whether the model remains robust with multi-source input;
- applicability to SOC-style hybrid IDS architecture.

### Why It Is Important

For a proposal focused on hybrid IDS and exfiltration detection, this dataset is especially important because it is closer to a real SOC architecture.

### Use in the Project

```text
TEST:
- hybrid host + network validation
- multi-source telemetry
- feature-level fusion
- SOC-style architecture check
```

---

## 8. ISOT Cloud IDS Dataset

### Role

**Evaluation of the model in a cloud environment.**

### Link

<https://www.uvic.ca/engineering/ece/isot/datasets/cloud-security/index.php>

### Fact

The ISOT Cloud IDS Dataset contains cloud environment telemetry: system logs, syscalls, and performance metrics.

### Contents

- system logs;
- syscalls;
- cloud performance metrics;
- cloud activity traces.

### Why It Is Needed

It is used to evaluate model transferability to cloud infrastructure.

### It Checks

- model transferability to cloud infrastructure;
- robustness to another type of host telemetry;
- detection under cloud workload conditions;
- applicability beyond local machines.

### Why It Is Important

If the project claims applicability not only to local machines but also to modern infrastructure, a cloud dataset strengthens the argument.

### Use in the Project

```text
TEST:
- cloud environment validation
- cloud workloads
- cloud logs / syscalls
- performance metrics
```

---

## 9. Dynamic Malware Analysis Dataset

### Role

**Evaluation of malware-driven host behavior.**

### Link

<https://zenodo.org/record/1203289>

### Fact

The Dynamic Malware Analysis Dataset is intended for analyzing malware behavior through kernel calls and user-level activity.

### Contents

- kernel calls;
- user-level activity;
- malware behavior traces.

### Why It Is Needed

It is used to extend the model to malware-driven host behavior.

### It Checks

- malware execution patterns;
- suspicious process behavior;
- signs of exfiltration-related activity;
- host-side malicious behavior.

### Why It Is Important

DNS exfiltration is often linked to malware or post-exploitation activity. This dataset helps connect host behavior with potential exfiltration logic.

### Use in the Project

```text
TEST:
- malware-driven host behavior
- suspicious process behavior
- exfiltration-related host activity
- malicious behavior traces
```

---

## 10. HDFS Log Dataset

### Role

**Additional baseline for log anomaly detection.**

### Link

<https://github.com/logpai/loghub>

### Fact

HDFS Log Dataset is a classic log anomaly detection dataset.

### Contents

- system logs;
- structured log sequences;
- anomaly labels.

### Why It Is Needed

It is used for additional experiments with log anomaly detection.

It is suitable for:

- quick experiments;
- evaluation of log anomaly methods;
- feature engineering on structured log sequences;
- comparison of anomaly detection approaches.

### Limitation

This is not a security-focused dataset. It is useful for testing log anomaly methods, but it should not be the main source for host intrusion detection.

### Use in the Project

```text
EXPERIMENTS:
- log anomaly experiments
- structured log sequences
- anomaly detection baseline
```

---

# 4. Correct Role Assignment

| Stage | Dataset | Purpose |
|---|---|---|
| TRAIN | ADFA IDS | baseline HIDS training |
| TRAIN | LID-DS 2021 | primary sequence modelling training |
| TRAIN | Maintainable Log Dataset | enterprise log behavior modelling |
| VALIDATION | LID-DS 2019 | cross-version validation on CVE-based attacks |
| VALIDATION | LANL Dataset | user / host behavior evaluation |
| VALIDATION | Windows Event Log / OTRF | SOC-style validation |
| TEST | Unified Host + Network Dataset / LANL | hybrid host + network test |
| TEST | ISOT Cloud IDS Dataset | cloud environment test |
| TEST | Dynamic Malware Analysis Dataset | malware behavior test |
| EXPERIMENTS | HDFS Log Dataset | log anomaly experiments |
| EXPERIMENTS | BGL Logs | non-security anomaly baseline |
| EXPERIMENTS | Syscall Dataset Generator | synthetic syscall augmentation |
| EXPERIMENTS | COMIDDS | search for additional datasets |

---

# 5. Correct Training Scheme

## TRAIN

```text
ADFA IDS
-> baseline normal / attack host traces
-> HIDS baseline
-> comparison with classic research approaches
```

```text
LID-DS 2021
-> syscall sequence modelling
-> Linux host behavior
-> LSTM / GRU / CNN-LSTM / Transformer models
```

```text
Maintainable Log Dataset
-> enterprise log behavior modelling
-> multi-stage attack behavior
-> feature-level fusion
```

## VALIDATION

```text
LID-DS 2019
-> CVE-based attack scenarios
-> cross-version validation
-> syscall-level robustness check
```

```text
LANL Dataset
-> user-host behavior
-> authentication behavior
-> lateral movement patterns
```

```text
Windows Event Logs / OTRF
-> SOC telemetry validation
-> Windows host behavior
-> Sysmon-style event analysis
```

## TEST

```text
Unified Host + Network Dataset / LANL
-> hybrid IDS validation
-> host + network correlation
-> multi-source telemetry test
```

```text
ISOT Cloud IDS Dataset
-> cloud environment validation
-> cloud logs / syscalls
-> cloud workload robustness
```

```text
Dynamic Malware Analysis Dataset
-> malware-driven host behavior
-> suspicious process behavior
-> exfiltration-related activity
```

## EXPERIMENTS

```text
HDFS Log Dataset
-> log anomaly experiments
-> structured log sequences
-> non-security anomaly baseline
```

```text
BGL Logs
-> non-security anomaly baseline
-> additional log anomaly experiments
```

```text
Syscall Dataset Generator
-> synthetic syscall augmentation
-> extra syscall traces
```

```text
COMIDDS
-> search for additional datasets
-> expansion of validation / test dataset set
```

---

# 6. Final Usage Logic

## Main Idea

The host-side part of the project should not rely on a single dataset because different sources cover different behavior layers:

```text
ADFA IDS provides a classic HIDS baseline.
LID-DS 2021 trains the model on syscall sequence modelling.
Maintainable Log Dataset adds enterprise multi-stage behavior.
LID-DS 2019 checks transferability inside the syscall-family datasets.
LANL checks user / authentication behavior.
Windows Event Logs / OTRF checks applicability to SOC telemetry.
Unified Host + Network Dataset checks hybrid host + network fusion.
ISOT Cloud IDS checks the cloud environment.
Dynamic Malware Analysis Dataset checks malware-driven host behavior.
HDFS / BGL are used only for anomaly experiments.
```

## Critical Logic

There are many datasets for host-based intrusion detection, but most of them cover only one data type:

- system calls;
- logs;
- authentication events;
- malware traces;
- cloud telemetry;
- network + host events.

A single host dataset rarely covers a complete attack scenario:

```text
process behavior
+ user behavior
+ enterprise logs
+ network correlation
+ cloud environment
+ malware-driven behavior
```

Therefore, for the host-side part of the project, it is better to use **feature-level fusion** instead of trying to mechanically combine raw logs, syscalls, and authentication events into one common dataset.

---

# 7. Minimum Required Configuration

For a serious host-side proposal, the minimum dataset set should be:

| Priority | Dataset | Status |
|---|---|---|
| 1 | ADFA IDS | required |
| 2 | LID-DS 2021 | required |
| 3 | Maintainable Log Dataset | required |
| 4 | LID-DS 2019 | recommended |
| 5 | LANL Dataset | recommended |
| 6 | Unified Host + Network Dataset / LANL | recommended |
| 7 | Windows Event Log / OTRF Security Datasets | recommended |
| 8 | ISOT Cloud IDS Dataset | optional |
| 9 | Dynamic Malware Analysis Dataset | optional |
| 10 | HDFS / BGL Logs | experiments only |

## Minimum Sufficient Stack

```text
ADFA IDS
LID-DS 2021
Maintainable Log Dataset
```

Without these three sources, the host-side part of the project would be insufficiently justified.

## Optimal Stack for the Proposal

```text
ADFA IDS
LID-DS 2021
LID-DS 2019
LANL Dataset
Maintainable Log Dataset
Unified Host + Network Dataset / LANL
```

This stack covers baseline HIDS, sequence modelling, validation, user-host behavior, enterprise multi-stage behavior, and hybrid validation.

## Advanced Stack

```text
ISOT Cloud IDS Dataset
Dynamic Malware Analysis Dataset
Windows Event Logs / OTRF
HDFS / BGL Logs
```

This stack strengthens cloud validation, malware behavior validation, SOC-style applicability, and additional anomaly experiments.

---

# 8. Short Conclusion

## Required

1. **ADFA IDS**: baseline HIDS training and comparability with classic research approaches.
2. **LID-DS 2021**: primary syscall sequence modelling training.
3. **Maintainable Log Dataset**: enterprise log behavior and multi-stage attack modelling.

## Recommended

4. **LID-DS 2019**: cross-version validation on CVE-based attacks.
5. **LANL Dataset**: user / authentication behavior and lateral movement patterns.
6. **Windows Event Log / OTRF Security Datasets**: SOC-style validation.
7. **Unified Host + Network Dataset / LANL**: hybrid host + network validation.

## Additional

8. **ISOT Cloud IDS Dataset**: cloud environment validation.
9. **Dynamic Malware Analysis Dataset**: malware-driven host behavior.
10. **HDFS / BGL Logs**: additional log anomaly experiments.

## Final Scheme

```text
TRAIN:
- ADFA IDS
- LID-DS 2021
- Maintainable Log Dataset

VALIDATION:
- LID-DS 2019
- LANL Dataset
- Windows Event Logs / OTRF

TEST:
- Unified Host + Network Dataset / LANL
- ISOT Cloud IDS Dataset
- Dynamic Malware Analysis Dataset

EXPERIMENTS:
- HDFS Log Dataset
- BGL Logs
- Syscall Dataset Generator
- COMIDDS
```
