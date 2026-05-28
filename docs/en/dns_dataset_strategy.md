# DNS Dataset Strategy (Current Scope)

## 1. Purpose
This document defines the DNS datasets currently used in the project.

Current DNS scope:
- `TRAIN`: attack + benign learning
- `VALIDATION`: false-positive control
- `TEST`: cross-dataset realism check
- DNS `EXPERIMENTS`: not used

## 2. Active DNS Datasets

### 2.1 CIC-Bell-DNS-EXF-2021
Role: `TRAIN` (attack-class behavior)

Use:
- DNS exfiltration / tunneling attack patterns
- temporal and tabular feature extraction for classifier + sequence branch

Link: <https://www.unb.ca/cic/datasets/dns-exf-2021.html>

### 2.2 CIC-Bell-DNS-2021
Role: `TRAIN` + `VALIDATION` (benign baseline and FP control)

Use:
- normal DNS behavior baseline
- benign-class balancing
- false-positive calibration

Link: <https://www.unb.ca/cic/datasets/dns-2021.html>

### 2.3 Mendeley DNS Exfiltration Dataset
Role: `TEST` (independent realism/generalization check)

Use:
- external validation on data with distribution shift
- robustness check for transferability

Link: <https://data.mendeley.com/datasets/c4n7fckkz3/3>

## 3. Role Matrix (Current)

| Role | Dataset | Purpose |
|---|---|---|
| `TRAIN` | CIC-Bell-DNS-EXF-2021 | attack behavior learning |
| `TRAIN` | CIC-Bell-DNS-2021 | benign behavior learning |
| `VALIDATION` | CIC-Bell-DNS-2021 split | false-positive control and threshold tuning |
| `TEST` | Mendeley DNS Exfiltration Dataset | cross-dataset realism / generalization |

## 4. Training / Validation / Test Scheme

```text
TRAIN:
  - CIC-Bell-DNS-EXF-2021
  - CIC-Bell-DNS-2021

VALIDATION:
  - CIC-Bell-DNS-2021 split

TEST:
  - Mendeley DNS Exfiltration Dataset
```

## 5. Scope Note
DNS branch uses only the datasets listed above.

## 6. Short Conclusion
Required and active DNS datasets:
1. `CIC-Bell-DNS-EXF-2021`
2. `CIC-Bell-DNS-2021`
3. `Mendeley DNS Exfiltration Dataset`
