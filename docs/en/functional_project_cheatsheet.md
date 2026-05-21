# Functional Project Cheatsheet (Hybrid Exfiltration Detection)

## 1. Core Focus (from proposal + datasets docs)
- Build a **behaviour-driven hybrid IDS** for data exfiltration detection.
- Combine **network telemetry + host telemetry** at the **feature level** (not raw log fusion).
- Model **multi-stage attack progression** (recon -> staging -> exfiltration), not only isolated anomalies.
- Keep explainability practical with **SHAP** so SOC analysts can validate why alerts fired.

## 2. What Must Work in a Functional MVP
- End-to-end pipeline from dataset ingestion to reproducible model evaluation.
- Two-level detection logic:
  - event/sample classification (RF, XGBoost, CNN);
  - sequence-level classification (LSTM over sliding windows).
- Late fusion of classifier probability + sequence probability.
- Evaluation with stratified CV and explicit false-positive control.
- Reproducible outputs: metrics, model artifacts, feature schema, experiment logs.

## 3. Mandatory Dataset Strategy (Do Not Mix Roles)

### DNS branch
- `TRAIN (attack)`: CIC-Bell-DNS-EXF-2021
- `TRAIN/VALIDATION (benign + FP control)`: CIC-Bell-DNS-2021
- `TEST (final benchmark)`: BCCC-CIC-Bell-DNS-2024
- `TEST (cross-dataset realism)`: Mendeley DNS Exfiltration Dataset
- `EXPERIMENTS only`: Kaggle DNS Tunneling (synthetic)

### Host branch
- `TRAIN`: ADFA IDS + LID-DS 2021 + Maintainable Log Dataset
- `VALIDATION`: LID-DS 2019 + LANL + OTRF Windows/Sysmon
- `TEST`: Unified Host+Network (LANL) + ISOT Cloud IDS + Dynamic Malware Analysis
- `EXPERIMENTS only`: HDFS/BGL and synthetic generators

## 4. Architectural Priorities for Production-Ready Growth
- Canonical event schema for all sources: timestamps, actor/process, network context, labels.
- Strict train/val/test split boundaries by source/time to avoid leakage.
- Separate feature builders:
  - network features (flow stats, DNS entropy, inter-arrival, frequency);
  - host features (syscall distributions, process patterns, privilege indicators, file-access entropy).
- Sequence builder with fixed windows (proposal suggests ~50-100 events/window).
- Explainability module:
  - global SHAP feature ranking;
  - local SHAP for TP/FP cases;
  - stability check across CV folds.

## 5. Minimum Practical Stack
- **Must-have datasets**:
  - DNS: EXF-2021 + DNS-2021 + BCCC-2024
  - Host: ADFA + LID-DS 2021 + Maintainable Log
- **Must-have models**:
  - RF/XGBoost as robust baselines
  - CNN for structured feature patterns
  - LSTM for temporal behaviour
- **Must-have metrics**:
  - Precision, Recall, F1 as primary
  - FPR and AUC as control metrics

## 6. Risks to Control Early
- Dataset incompatibility between host/network sources -> use feature-level integration and documented mapping.
- Class imbalance -> weighted losses/sampling and threshold tuning on validation only.
- Overfitting to one dataset family -> cross-dataset tests (BCCC, Mendeley, LID-DS 2019, LANL).
- Compute limits -> keep baseline-first training order, then add CNN/LSTM iterations.

## 7. 12-Week Execution Spine (from proposal)
1. Phase 1: dataset access + feature engineering + ATT&CK mapping.
2. Phase 2: hybrid classifier pipeline implementation.
3. Phase 3: LSTM sequence module and integration.
4. Phase 4: SHAP integration and interpretation quality checks.
5. Phase 5: ablation + benchmark comparisons + final validation.

## 8. Done Criteria for “Functional Project”
- Full reproducible run from raw source files to final test report.
- Documented config for dataset role mapping and split policy.
- Saved artifacts: models, thresholds, feature lists, SHAP summaries.
- Test report includes:
  - per-dataset metrics;
  - FP analysis;
  - ablation table (no-sequence vs sequence, no-host vs hybrid);
  - known limitations and next-step plan.

## 9. Repo-Level Implementation Hint
- `manage.py`: orchestrator for stages (`prepare`, `train`, `eval`, `explain`, `report`).
- `scripts/`: idempotent data preparation, feature build, training/eval runners.
- `docs/en|ru`: keep architecture decisions, dataset-role matrix, and reproducibility instructions synchronized.
