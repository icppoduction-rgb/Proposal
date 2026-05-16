# Host Dataset Cleanup Report — datasets-new/host

**Date:** 2026-05-16

---

## 1. Summary

Redundant converted host datasets belonging to extended, optional, or experimental validation were removed from the `datasets-new/host` directory. The minimum sufficient host stack required for the thesis has been retained:

| Dataset | Purpose |
|:---|:---|
| **ADFA IDS** | Baseline HIDS training |
| **LID-DS 2021** | Syscall sequence modelling |
| **Maintainable Log Dataset** | Enterprise multi-stage log behaviour |

This set corresponds to the minimum required configuration defined in `docs/en/host_datasets_analysis.md` and covers the core proposal objectives: baseline HIDS, syscall sequence modelling, and enterprise multi-stage log behaviour.

---

## 2. Why the Cleanup Was Performed

The document `docs/en/project_proposal_analysis.md` identifies several important project constraints:

- the research must be reproducible;
- public datasets must be explicitly selected and justified;
- there is a risk of incompatibility between host and network datasets;
- there are constraints on time, data availability, and computational resources;
- a thesis project does not require storing all possible validation/test/experiment datasets.

> An engineering decision was therefore made to retain only the core datasets required for the main research track, and to remove the large extended datasets from `datasets-new/host`.

---

## 3. Retained Datasets

---

### ADFA IDS

> **Reason:** Primary baseline dataset for Host-Based Intrusion Detection.

Needed for initial comparison with classic HIDS approaches and for training on normal/attack host traces.

---

### LID-DS 2021

> **Reason:** Primary dataset for syscall sequence modelling.

Needed for the LSTM/CNN-LSTM part of the project and for analysing process behaviour over time.

---

### Maintainable Log Dataset

> **Reason:** Primary dataset for enterprise logs and multi-stage attack modelling.

Needed to ensure the project covers not only syscall-level behaviour but also log-level behavioural patterns.

---

## 4. Removed Datasets

---

### Dynamic Malware Analysis Dataset

| Parameter | Value |
|:---|:---|
| Files removed | 298,625 |
| Size | ~41.49 GiB |

> **Reason for removal:** This is a malware-driven validation dataset. It is useful for extended evaluation of suspicious process behaviour, but it is optional for the current thesis scope and occupies the largest disk volume.

---

### LID-DS 2019

| Parameter | Value |
|:---|:---|
| Files removed | 6,502 |
| Size | ~6.06 GiB |

> **Reason for removal:** This is a cross-version validation dataset for CVE-based attacks. It is useful for additional model transferability checks, but the minimum thesis stack already includes LID-DS 2021 as the primary sequence dataset.

---

### Windows Event Log / OTRF Security Datasets

| Parameter | Value |
|:---|:---|
| Files removed | 246 |
| Size | ~246.11 MiB |

> **Reason for removal:** This is a SOC-style Windows telemetry validation dataset. It is desirable for extending practical SOC validation, but it is not required for the baseline implementation of the proposal.

---

### Unified Host + Network Dataset / LANL

| Parameter | Value |
|:---|:---|
| Files removed | 5 |
| Size | ~15.38 MiB |

> **Reason for removal:** This is a hybrid host+network validation dataset. It is useful for extended feature-level fusion evaluation, but the current objective is to reduce the host dataset volume to the minimum required thesis set.

---

### LANL Dataset

| Parameter | Value |
|:---|:---|
| Files removed | 5 |
| Size | ~15.38 MiB |

> **Reason for removal:** This is an enterprise user-host/authentication behaviour validation dataset. It belongs to the desirable validation tier but is not part of the minimum required configuration.

---

### ISOT Cloud IDS Dataset

| Parameter | Value |
|:---|:---|
| Files removed | 3 |
| Size | ~12.71 MiB |

> **Reason for removal:** This is a cloud environment validation dataset. It is optional and only needed if the project separately demonstrates model transferability to cloud workloads.

---

### HDFS Log Dataset

| Parameter | Value |
|:---|:---|
| Files removed | 6 |
| Size | ~12.44 MiB |

> **Reason for removal:** This is an experiments-only log anomaly dataset. It is not a security-focused host intrusion dataset and is only needed for additional log anomaly detection experiments.

---

## 5. Cleanup Results

### Before Cleanup

| Parameter | Value |
|:---|:---|
| Files in `datasets-new/host` | 392,084 converted JSON files |

### Removed

| Parameter | Value |
|:---|:---|
| Files | 305,392 |
| Size | ~47.84 GiB |

### Remaining

| Parameter | Value |
|:---|:---|
| Files | 86,692 |
| Size | ~4.63 GiB |

---

### Final State by Split

| Split | Files | Size |
|:---:|---:|---:|
| `TRAIN` | 72,373 | ~3,083.34 MiB |
| `VALIDATION` | 10,799 | ~569.46 MiB |
| `TEST` | 3,520 | ~1,090.44 MiB |
| `EXPERIMENTS` | 0 | — |

---

## 6. How to Verify

### Dry-run check

```bash
python scripts/cleanup_host_datasets_new.py --root datasets-new/host --workers 16
```

**Expected result after cleanup:**

```
Deleted files: 0
```

---

### Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

**Expected result:**

```
OK
```
