# Functional Project Cheatsheet

## 1. Project Goal
Design and evaluate a behaviour-driven hybrid ML framework for multi-stage data exfiltration detection by combining host telemetry, network traffic features, sequence modelling, and explainability.

## 2. Main Research Focus
- Identify cross-domain behavioural indicators (host + network) for exfiltration stages.
- Build a hybrid architecture combining classical ML and DL.
- Model temporal attack progression (not only event-level anomalies).
- Improve operational interpretability with SHAP.

## 3. Core Architecture
- **Layer 1: Multi-source integration**: ingest, preprocess, normalize host/network features into unified feature representation.
- **Layer 2: Hybrid ML/DL classifier**: Random Forest, XGBoost, CNN for event/sample-level malicious vs benign classification.
- **Layer 3: Behavioural sequence modelling**: LSTM over ordered behavioural events.
- **Decision logic**: late fusion of classifier and sequence-model probabilities.

## 4. Dataset Strategy
- Keep strict role separation: `TRAIN`, `VALIDATION`, `TEST`, `EXPERIMENTS`.
- Do not mix DNS and host dataset logic in one role table; manage them independently.
- Use feature-level integration across heterogeneous sources (not raw one-to-one log fusion).

## 5. DNS Dataset Roles
| Role | Dataset(s) | Purpose |
|---|---|---|
| `TRAIN` | CIC-Bell-DNS-EXF-2021 | Attack-class training (DNS exfiltration/tunneling). |
| `TRAIN` | CIC-Bell-DNS-2021 | Benign-class training (normal DNS behaviour). |
| `VALIDATION` | CIC-Bell-DNS-2021 split | False-positive control, threshold tuning. |
| `TEST` | BCCC-CIC-Bell-DNS-2024 | Final benchmark, generalization, overfitting check. |
| `TEST` | Mendeley DNS Exfiltration | Cross-dataset realism/transferability check. |
| `EXPERIMENTS` | Kaggle DNS Tunneling | Fast prototyping, feature experiments, augmentation only. |

## 6. Host Dataset Roles
| Role | Dataset(s) | Purpose |
|---|---|---|
| `TRAIN` | ADFA IDS | Baseline HIDS training. |
| `TRAIN` | LID-DS 2021 | Primary syscall sequence modelling. |
| `TRAIN` | Maintainable Log Dataset | Enterprise log + multi-stage behaviour modelling. |
| `VALIDATION` | LID-DS 2019 | Cross-version/CVE robustness validation. |
| `VALIDATION` | LANL | User-host/authentication/lateral movement validation. |
| `VALIDATION` | Windows Event Log / OTRF | SOC-style Windows telemetry validation. |
| `TEST` | Unified Host + Network / LANL | Hybrid host+network robustness test. |
| `TEST` | ISOT Cloud IDS | Cloud transferability test. |
| `TEST` | Dynamic Malware Analysis | Malware-driven host behaviour test. |
| `EXPERIMENTS` | HDFS, BGL, Syscall Generator, COMIDDS | Auxiliary anomaly experiments/augmentation/dataset search. |

## 7. Feature Engineering Focus
- Network features: flow stats, packet size patterns, inter-arrival timing, DNS entropy, communication frequency.
- Host features: syscall frequencies, file-access entropy, process execution patterns, privilege usage.
- Use MITRE ATT&CK mapping as intermediate alignment for attack-stage indicators.
- Validate feature importance with SHAP.

## 8. Sequence Modelling Focus
- Use LSTM for temporal dependencies in multi-stage behaviour.
- Build ordered event sequences using sliding windows.
- Sequence size target: ~50-100 events per sequence.
- Sequence-level binary classification: benign vs exfiltration.

## 9. Explainability Focus
- SHAP is the primary XAI method.
- Produce both global and local feature attributions.
- Qualitative check: TP/FP case explanations per CV fold vs MITRE stage logic.
- Quantitative check: SHAP rank-order consistency across CV folds.

## 10. Implementation Priorities
1. Finalize dataset access and role-separated splits.
2. Implement feature engineering + ATT&CK-aligned feature schema.
3. Build baseline hybrid classifier (RF/XGBoost/CNN).
4. Integrate LSTM sequence layer + late fusion.
5. Add SHAP pipeline and explanation quality checks.
6. Run stratified k-fold CV, ablation, and cross-dataset validation.

## 11. Project Constraints
- Timeline: 12 weeks (May-Aug 2026), 5 phased methodology.
- Public benchmark datasets only; no live traffic capture.
- Scope-limited model set: RF, XGBoost, CNN, LSTM.
- Out of scope: RL components, graph-based extensions, full unsupervised sequence modelling, large-scale raw multi-dataset fusion.
- Class imbalance expected; prioritize precision/recall/F1 (+ AUC, FPR).

## 12. What Not To Do
- Do not train on datasets assigned for `TEST`.
- Do not use synthetic Kaggle DNS tunneling data as final evidence of model quality.
- Do not collapse DNS and host role logic into one mixed dataset pipeline.
- Do not rely on payload inspection assumptions for encrypted channels (scope is metadata/behavioural modelling).
- Do not skip false-positive validation on benign-heavy distributions.

## 13. Recommended Development Order
1. Lock dataset inventory and role matrix for DNS and host streams separately.
2. Implement shared preprocessing contracts and feature dictionaries.
3. Train baseline non-sequential models and establish reference metrics.
4. Add LSTM sequence branch and late-fusion decision layer.
5. Integrate SHAP reports (global/local + fold consistency checks).
6. Execute full evaluation suite: stratified CV, ablation, cross-dataset generalization.
7. Freeze reproducible experiment configs and reporting templates.
