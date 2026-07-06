# Repository state, QA, and gaps

This document merges `repository_qa_section_3_8.md`, QA content from `project_proposal_analysis.md`, and constraints from `functional_project_cheatsheet.md`. Its purpose is to separate implemented repository state from proposal-level plans.

## Analysis scope

The original QA document recorded a repository review across `scripts`, `docs`, `report`, `planning`, `temp_data`, `logs`, and project configs. The key conclusion remains:

> The current repository confirms dataset preparation, Stage Two normalization, and Stage Three feature/model-ready preparation. Model training and evaluation remain Stage Four.

## Confirmed implementation

| Area | Confirmed |
| --- | --- |
| Stage One dataset preparation | Dataset scanning, role assignment, host filtering, format sorting, JSON path maps. |
| DNS datasets | `CIC-Bell-DNS-2021` (`TRAIN` + `VALIDATION`), `CIC-Bell-DNS-EXF-2021` (`TRAIN`), `Mendeley-DNS-Exfiltration-Dataset` (`TEST`). |
| Host datasets | `TRAIN`: ADFA IDS, LID-DS 2021, Maintainable Log Dataset; `VALIDATION`: LID-DS 2019, LANL, Windows Event Log / OTRF; `TEST`: Dynamic Malware Analysis, ISOT Cloud IDS, Unified Host-Network / LANL. |
| Pipeline separation | DNS and Host are processed as separate branches. |
| Confirmed volumes | DNS sorted/exported files: 35; Host filtered kept paths: 361646 in the old QA; 361670 total files in the current analysis-dataset summary across 64 buckets. |
| Stage Two normalization | Implemented CLI routes cover storage bootstrap, catalog ingestion, parser registry seeding, parser coverage, mark-ready, exact bucket normalization, benchmark runs, large line-based file splitting, DuckDB checks, leakage checks, and traceability. |
| Stage Three feature/model-ready preparation | The `python manage.py stage-three ...` CLI is implemented for readiness gate, feature catalog, runtime backend probe, feature extraction, label alignment, sequence build, model-ready build, quality checks, leakage/traceability checks, and final report. |
| Stage Three reports | Task01-Task20 reports are written under `PATH_DATA_STORAGE/reports/{ru,en}/stage-three`; `final-report` explicitly returns `READY_FOR_STAGE_FOUR` or `NOT_READY_FOR_STAGE_FOUR`. |
| Current docs | Stage One/Stage Two/Stage Three architecture, normalization, parser strategy, labels, leakage, performance controls, and traceability are documented in `analysis-dataset/`, `normalization/`, `stage-three/`, and `code-documentation/`. |

## Proposal-level, not confirmed implementation

| Area | Proposal-level statement | Gap |
| --- | --- | --- |
| Physical resampling strategy | SMOTE/undersampling as a production default. | Stage Three supports class balance reporting and TRAIN-only balancing constraints; SMOTE should not become default before separate validation. |
| Random Forest / XGBoost | Baseline classifiers. | Parameters, training code, and tuning are not fixed. |
| CNN | Deep learning branch for local feature patterns. | Architecture not specified. |
| LSTM | Sequence-level binary classification, 50-100 events per sequence. | Stage Three can prepare sequence artifacts; LSTM model, training config, and evaluation remain Stage Four. |
| Late fusion | Aggregation of classifier + sequence probabilities. | Formula/weights/threshold are not specified. |
| SHAP | Feature attribution and rank stability. | TreeSHAP/DeepSHAP/KernelSHAP are not selected or implemented. |
| Evaluation | Stratified k-fold CV, ablation, baseline comparisons. | `k`, statistical tests, seeds, and reports are not fixed. |
| Runtime environment | Cloud fallback, hardware assumptions. | Hardware and ML library versions are not specified; `requirements.txt` contains only `python-dotenv` and `rich` without pinned versions. |

## Current implementation notes

Checked against code on 2026-07-04:

- Stage Two command routing is in `scripts/stage_two/cli.py`; `config.manage_commands` is an older printed command list and is not complete for current Stage Two commands.
- `normalize-format` and `benchmark-normalization` apply resource profiles and format-specific runtime policy before execution. `normalize-all` resolves shared runtime options but does not apply per-format policy in the CLI route.
- The implemented quality gates are parser reports, post-run validation for `normalize-format`, DuckDB checks, leakage checks, and traceability lookup. They are checks around normalized/features/model-ready artifacts, not a complete ML experiment pipeline.
- The repository now confirms the Stage Three CLI for feature extraction, model-ready build, checks, and final report. RF/XGBoost/CNN/LSTM training, SHAP analysis, and evaluation reports remain unimplemented Stage Four work.

## QA for proposal sections 3.3-3.8

| Question | Answer |
| --- | --- |
| Which datasets were used? | DNS and Host datasets are listed in [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md). |
| Are total samples / class split / feature count known? | Mostly no. `CIC-Bell-DNS-2021` is documented as about 1,000,000 domains and about 99% benign, but most sources lack confirmed counts. |
| Are network and host separate datasets? | Yes, separate datasets and separate pipelines. |
| Were host features simulated from network data? | No such implementation was found; feature-level simulation is proposal-level only. |
| Missing values / scaling / categorical encoding? | Implemented as Stage Three preprocessing utilities and reports; production readiness depends on the concrete `experiment_id` and final checks. |
| Class imbalance methods? | Stage Three provides class balance reports and class-weight metadata; physical resampling is TRAIN-only and not the DNS MVP default. |
| Model configs? | RF/XGBoost/CNN/LSTM configs are not specified. |
| Sequence construction? | Stage Three contains a sequence/window builder; production length, step, overlap, and alignment policy must be fixed per experiment. |
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

1. Run `stage-three final-report` for every `experiment_id` and do not move to Stage Four without `READY_FOR_STAGE_FOUR`.
2. Expand the production Stage Three path to Host/Network/Hybrid feature groups after DNS MVP.
3. Fix production sequence window policy: length, step, overlap, label assignment, and time alignment.
4. Add Stage Four model configs for RF/XGBoost/CNN/LSTM.
5. Define late fusion formula and threshold policy.
6. Select SHAP variants by model family.
7. Add experiment config: CV folds, random seeds, hardware/software versions, statistical tests.
8. Add Stage Four training/evaluation reports.

## Related documents

- [project_overview_and_research_context.md](project_overview_and_research_context.md)
- [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md)
- [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md)
- [analysis-dataset/README.md](analysis-dataset/README.md)
- [normalization/README.md](normalization/README.md)
- [stage-three/README.md](stage-three/README.md)
- [code-documentation/README.md](code-documentation/README.md)
