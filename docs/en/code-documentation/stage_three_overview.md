# Stage Three Overview

Stage Three converts Stage Two normalized Parquet artifacts into feature artifacts and model-ready artifacts for Stage Four.

Responsibility boundary:

```text
Stage Two:   raw -> normalized
Stage Three: normalized -> features -> model-ready
Stage Four:  model-ready -> training/evaluation/explainability
```

Stage Three does not train RF/XGBoost/CNN/LSTM models, tune thresholds, or produce SHAP explanations.

## CLI

Entry point: `python manage.py stage-three ...`.

Actual router: `scripts/stage_three/cli.py`.

Supported commands:

| Command | Purpose |
| --- | --- |
| `validate-inputs` | Checks Stage Two normalized artifacts before downstream Stage Three work. |
| `build-feature-catalog` | Validates `feature_catalog.yml` and writes the normalized JSON snapshot. |
| `probe-runtime-backend` | Resolves CPU/GPU backend and memory guard profile. |
| `extract-features` | Reads normalized Parquet and writes feature artifacts. |
| `align-labels` | Fixes label policy without putting labels into X. |
| `build-sequences` | Creates sequence/window artifacts for Stage Four DL branches. |
| `build-model-ready` | Builds X/y/metadata/traceability, split index, and preprocessing metadata. |
| `rebalance-dns-supervised` | Builds a reproducible DNS supervised 70/30 model-ready split for a baseline experiment. |
| `run-quality-checks` | Checks feature/model-ready/preprocessing artifacts. |
| `run-leakage-checks` | Checks forbidden X columns, TEST leakage, fit role, and traceability. |
| `trace-artifact` | Resolves model-ready lineage back to raw source. |
| `final-report` | Writes the Task20 final report and Stage Four readiness status. |

## Modules

| Package | Purpose |
| --- | --- |
| `scripts/stage_three/requests.py` | Typed request dataclasses for the CLI. |
| `scripts/stage_three/storage/` | Stage Three storage directory bootstrap. |
| `scripts/stage_three/readiness/` | Stage Three input readiness gate. |
| `scripts/stage_three/feature_catalog/` | YAML/JSON feature catalog loader, validator, reports. |
| `scripts/stage_three/runtime/` | Resource profile, memory guard, CPU/GPU backend selection. |
| `scripts/stage_three/extraction/` | DNS/Host/Network extractors, artifact writer, registry integration. |
| `scripts/stage_three/labels/` | Label policies for windows/sequences. |
| `scripts/stage_three/preprocessing/` | Type casting, missing values, categorical encoding, scaling profiles, class balance. |
| `scripts/stage_three/model_ready/` | X/y separation, split index, sequence builder, model-ready registry/builder. |
| `scripts/stage_three/quality/` | Feature quality, preprocessing quality, model-ready quality, leakage, traceability. |
| `scripts/stage_three/reports/` | Report path utilities, console output helpers, and final Task20 report generation. |

## Artifact Lifecycle

1. `validate-inputs` confirms Stage Two artifacts are usable.
2. `build-feature-catalog` validates allowed feature groups and forbidden X columns.
3. `extract-features` creates Parquet feature artifacts and registers `feature_artifacts`.
4. `align-labels` and model-ready separation keep labels outside X.
5. `build-model-ready` writes `X`, `y`, `metadata`, `traceability`, `split_index`, `preprocessing_metadata`.
6. `rebalance-dns-supervised` can create a separate DNS supervised baseline experiment without physically deleting raw files.
7. `run-quality-checks` registers `data_quality_reports`.
8. `run-leakage-checks` blocks unsafe artifacts with `BLOCKED_BY_LEAKAGE` or `BLOCKED_BY_QUALITY`.
9. `final-report` summarizes readiness for Stage Four.

## Readiness Policy

Stage Four may start only when:

- required model-ready artifacts exist for TRAIN/VALIDATION/TEST;
- quality checks have no blocking failures;
- leakage checks pass;
- traceability chain is recoverable;
- `stage-three final-report` returns `READY_FOR_STAGE_FOUR`.

If the PostgreSQL Catalog is unavailable, `final-report` still writes RU/EN reports but marks readiness as `NOT_READY_FOR_STAGE_FOUR`.

## Related Docs

- [../stage-three/README.md](../stage-three/README.md)
- [../stage-three/usage_guide.md](../stage-three/usage_guide.md)
- [../stage-three/stage_three_commands.md](../stage-three/stage_three_commands.md)
- [traceability.md](traceability.md)
- [data_leakage_prevention.md](data_leakage_prevention.md)
