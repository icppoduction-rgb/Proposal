# Key project documentation index

This index replaces the scattered top-level documents and shows where the key information on the proposal, dataset strategy, feature engineering, and the actual repository state has moved.

## Final structure

| Document | Purpose |
| --- | --- |
| [repository_analysis.md](repository_analysis.md) | Current repository analysis: entrypoints, CLI routing, Stage One/Two/Three, storage, tests, and gaps. |
| [project_overview_and_research_context.md](project_overview_and_research_context.md) | Research context, proposal-level architecture, questions, objectives, methodology, scope, plan, and limitations. |
| [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md) | Unified DNS and Host dataset strategy with explicit `TRAIN` / `VALIDATION` / `TEST` separation. |
| [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md) | Feature extraction map, feature catalogue groups, schema requirements, leakage exclusions, and implementation priorities. |
| [stage-three/README.md](stage-three/README.md) | Stage Three feature/model-ready preparation: usage guide, commands, performance tuning, MVP DNS path, and production path. |
| [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md) | Confirmed repository state, proposal-vs-implementation boundaries, QA for sections 3.3-3.8, gaps, and follow-up work. |

## Merged legacy documents

| Old document | Content moved to |
| --- | --- |
| `project_proposal_analysis.md` | `project_overview_and_research_context.md`, `repository_state_qa_and_gaps.md`. |
| `functional_project_cheatsheet.md` | `project_overview_and_research_context.md`, `dataset_strategy_dns_host.md`, `feature_extraction_and_catalogue.md`. |
| `dns_dataset_strategy.md` | `dataset_strategy_dns_host.md`. |
| `host_datasets_analysis.md` | `dataset_strategy_dns_host.md`, `repository_state_qa_and_gaps.md`. |
| `dataset_feature_extraction_map.md` | `feature_extraction_and_catalogue.md`, `dataset_strategy_dns_host.md`. |
| `feature_catalogue_full.md` | `feature_extraction_and_catalogue.md`. |
| `repository_qa_section_3_8.md` | `repository_state_qa_and_gaps.md`. |

## Related current sections

- [analysis-dataset/README.md](analysis-dataset/README.md) — factual Stage One bucket/format/readiness analysis.
- [normalization/README.md](normalization/README.md) — Stage Two normalization guide.
- [stage-three/README.md](stage-three/README.md) — Stage Three feature extraction, preprocessing, and model-ready guide.
- [code-documentation/README.md](code-documentation/README.md) — code architecture, CLI, Stage One/Stage Two, DB, and parser strategy.

## Reading order

1. For current-code verification, read [repository_analysis.md](repository_analysis.md), then [repository_state_qa_and_gaps.md](repository_state_qa_and_gaps.md).
2. For the research proposal, read [project_overview_and_research_context.md](project_overview_and_research_context.md).
3. For dataset selection, read [dataset_strategy_dns_host.md](dataset_strategy_dns_host.md).
4. For feature engineering implementation, read [feature_extraction_and_catalogue.md](feature_extraction_and_catalogue.md).
5. For running Stage Three, read [stage-three/usage_guide.md](stage-three/usage_guide.md) and [stage-three/stage_three_commands.md](stage-three/stage_three_commands.md).

## Architecture invariants

- `TRAIN`, `VALIDATION`, and `TEST` are not mixed.
- `TEST` is not used for training, fit preprocessing, feature selection, or threshold tuning.
- DNS and Host logic are separated; integration happens only through normalized events, windows, features, and traceability.
- Labels are target/audit fields, not input features.
- A missing label does not mean benign.
- Proposal-level ideas are not documented as implemented unless confirmed by code, artifacts, or Stage Two/Stage Three documentation.
- Stage Three artifacts are ready for Stage Four only after `final-report` returns `READY_FOR_STAGE_FOUR`.
