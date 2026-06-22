# Repository state, QA, and gaps

This document merges `repository_qa_section_3_8.md`, QA content from `project_proposal_analysis.md`, and constraints from `functional_project_cheatsheet.md`. Its purpose is to separate implemented repository state from proposal-level plans.

## Analysis scope

The original QA document recorded a repository review across `scripts`, `docs`, `report`, `planning`, `temp_data`, `logs`, and project configs. The key conclusion remains:

> The current repository confirms the dataset preparation stage, not model training/evaluation.

## Confirmed implementation

| Area | Confirmed |
| --- | --- |
| Stage One dataset preparation | Dataset scanning, role assignment, host filtering, format sorting, JSON path maps. |
| DNS datasets | `CIC-Bell-DNS-2021` (`TRAIN` + `VALIDATION`), `CIC-Bell-DNS-EXF-2021` (`TRAIN`), `Mendeley-DNS-Exfiltration-Dataset` (`TEST`). |
| Host datasets | `TRAIN`: ADFA IDS, LID-DS 2021, Maintainable Log Dataset; `VALIDATION`: LID-DS 2019, LANL, Windows Event Log / OTRF; `TEST`: Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network / LANL. |
| Pipeline separation | DNS and Host are processed as separate branches. |
| Confirmed volumes | DNS sorted/exported files: 35; Host filtered kept paths: 361646 in the old QA; 361675 total files in the current analysis-dataset summary across 66 buckets. |
| Current docs | Stage One/Stage Two architecture, normalization, parser strategy, labels, leakage, and traceability are documented in `analysis-dataset/`, `normalization/`, and `code-documentation/`. |

## Proposal-level, not confirmed implementation

| Area | Proposal-level statement | Gap |
| --- | --- | --- |
| ML preprocessing | Missing value handling, scaling, categorical encoding. | No confirmed `MinMaxScaler`, `StandardScaler`, encoders, or fit pipeline. |
| Class imbalance | SMOTE/undersampling/class weights. | Implementation not found. |
| Random Forest / XGBoost | Baseline classifiers. | Parameters, training code, and tuning are not fixed. |
| CNN | Deep learning branch for local feature patterns. | Architecture not specified. |
| LSTM | Sequence-level binary classification, 50-100 events per sequence. | Sequence builder, step/overlap, alignment, and model config are not implemented. |
| Late fusion | Aggregation of classifier + sequence probabilities. | Formula/weights/threshold are not specified. |
| SHAP | Feature attribution and rank stability. | TreeSHAP/DeepSHAP/KernelSHAP are not selected or implemented. |
| Evaluation | Stratified k-fold CV, ablation, baseline comparisons. | `k`, statistical tests, seeds, and reports are not fixed. |
| Runtime environment | Cloud fallback, hardware assumptions. | Hardware and ML library versions are not specified; `requirements.txt` contains only `python-dotenv` and `rich` without pinned versions. |

## QA for proposal sections 3.3-3.8

| Question | Answer |
| --- | --- |
| Which datasets were used? | DNS and Host datasets are listed in [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md). |
| Are total samples / class split / feature count known? | Mostly no. `CIC-Bell-DNS-2021` is documented as about 1,000,000 domains and about 99% benign, but most sources lack confirmed counts. |
| Are network and host separate datasets? | Yes, separate datasets and separate pipelines. |
| Were host features simulated from network data? | No such implementation was found; feature-level simulation is proposal-level only. |
| Missing values / scaling / categorical encoding? | Not confirmed in code. |
| Class imbalance methods? | SMOTE, undersampling, class weights, or similar methods are not confirmed. |
| Model configs? | RF/XGBoost/CNN/LSTM configs are not specified. |
| Sequence construction? | Proposal says 50-100 events, but step/overlap/alignment are not specified. |
| Decision fusion? | Proposal says late fusion, but weights/formula/threshold are not specified. |
| SHAP variants? | Not specified. |
| Experimental environment? | CV folds, statistical tests, hardware, ML versions, and random seed are not specified. |

## Risks and recommendations

| Risk | Where it occurs | Consequence | Recommendation |
| --- | --- | --- | --- |
| Host/network dataset incompatibility | Dataset strategy / hybrid architecture. | Raw-level correlation cannot be proven. | Use feature-level integration and document assumptions. |
| TEST leakage | Feature extraction / model-ready artifacts. | Inflated evaluation. | Prohibit TEST for training, fit preprocessing, feature selection, threshold tuning. |
| Label leakage | Filename/scenario/path fields. | Model learns source instead of behaviour. | Exclude label/source/path/scenario fields from X. |
| Weak labels | Filename, IDS alert, scenario metadata. | Wrong supervised target. | Use `label_status`, confidence, and mapping rules. |
| Missing timestamps | TXT/trace/binary sources. | Invalid temporal features. | Use `timestamp=null`, `timestamp_type=missing`, or event order; never insert current time. |
| Large files | PCAP, BSON, JSON, netflow, txt traces. | Memory/performance failures. | Streaming parsers, batch writes, DuckDB/Parquet checks. |
| Schema drift | Mixed CSV/JSON/log schemas. | Broken normalization/features. | Schema-aware parsers and per-format quality reports. |
| Explainability over proxy fields | SHAP / model-ready X. | Misleading explanations. | Run leakage checks before SHAP and keep audit fields separate. |

## Follow-up tasks

1. Convert the feature catalogue into a machine-readable `feature_catalog.yml/json`.
2. Implement Stage Two feature extraction layers from [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md).
3. Add preprocessing contracts: missing values, categorical encoding, scaling, fit/transform separation.
4. Add model configs for RF/XGBoost/CNN/LSTM.
5. Define sequence window policy: length, step, overlap, label assignment, time alignment.
6. Define late fusion formula and threshold policy.
7. Select SHAP variants by model family.
8. Add experiment config: CV folds, random seeds, hardware/software versions, statistical tests.
9. Extend data quality reports: class balance, label coverage, timestamp coverage, schema drift, leakage.

## Related documents

- [project_overview_and_research_context.md](project_overview_and_research_context.md)
- [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md)
- [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md)
- [analysis-dataset/README.md](analysis-dataset/README.md)
- [normalization/README.md](normalization/README.md)
- [code-documentation/README.md](code-documentation/README.md)
