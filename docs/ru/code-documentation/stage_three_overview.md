# Stage Three overview

Stage Three превращает normalized Parquet artifacts из Stage Two в feature artifacts и model-ready artifacts для Stage Four.

Граница ответственности:

```text
Stage Two:   raw -> normalized
Stage Three: normalized -> features -> model-ready
Stage Four:  model-ready -> training/evaluation/explainability
```

Stage Three не обучает RF/XGBoost/CNN/LSTM, не подбирает thresholds и не строит SHAP explanations.

## CLI

Точка входа: `python manage.py stage-three ...`.

Фактический router: `scripts/stage_three/cli.py`.

Поддержанные команды:

| Команда | Назначение |
| --- | --- |
| `validate-inputs` | Проверяет Stage Two normalized artifacts перед downstream Stage Three. |
| `build-feature-catalog` | Валидирует `feature_catalog.yml` и пишет normalized JSON snapshot. |
| `probe-runtime-backend` | Резолвит CPU/GPU backend и memory guard profile. |
| `extract-features` | Читает normalized Parquet и пишет feature artifacts. |
| `align-labels` | Фиксирует label policy без помещения labels в X. |
| `build-sequences` | Создает sequence/window artifacts для Stage Four DL branches. |
| `build-model-ready` | Собирает X/y/metadata/traceability, split index и preprocessing metadata. |
| `run-quality-checks` | Проверяет feature/model-ready/preprocessing artifacts. |
| `run-leakage-checks` | Проверяет forbidden X columns, TEST leakage, fit role и traceability. |
| `trace-artifact` | Восстанавливает lineage model-ready artifact до raw source. |
| `final-report` | Пишет Task20 final report и Stage Four readiness status. |

## Модули

| Пакет | Назначение |
| --- | --- |
| `scripts/stage_three/requests.py` | Typed request dataclasses для CLI. |
| `scripts/stage_three/storage/` | Bootstrap Stage Three storage directories. |
| `scripts/stage_three/readiness/` | Stage Three input readiness gate. |
| `scripts/stage_three/feature_catalog/` | YAML/JSON feature catalog loader, validator, reports. |
| `scripts/stage_three/runtime/` | Resource profile, memory guard, CPU/GPU backend selection. |
| `scripts/stage_three/extraction/` | DNS/Host/Network extractors, artifact writer, registry integration. |
| `scripts/stage_three/labels/` | Label policies for windows/sequences. |
| `scripts/stage_three/preprocessing/` | Type casting, missing values, categorical encoding, scaling profiles, class balance. |
| `scripts/stage_three/model_ready/` | X/y separation, split index, sequence builder, model-ready registry/builder. |
| `scripts/stage_three/quality/` | Feature quality, preprocessing quality, model-ready quality, leakage, traceability. |
| `scripts/stage_three/reports/` | Report path utilities and final Task20 report generation. |

## Artifact lifecycle

1. `validate-inputs` confirms Stage Two artifacts are usable.
2. `build-feature-catalog` validates allowed feature groups and forbidden X columns.
3. `extract-features` creates Parquet feature artifacts and registers `feature_artifacts`.
4. `align-labels` and model-ready separation keep labels outside X.
5. `build-model-ready` writes `X`, `y`, `metadata`, `traceability`, `split_index`, `preprocessing_metadata`.
6. `run-quality-checks` registers `data_quality_reports`.
7. `run-leakage-checks` blocks unsafe artifacts with `BLOCKED_BY_LEAKAGE` or `BLOCKED_BY_QUALITY`.
8. `final-report` summarizes readiness for Stage Four.

## Readiness policy

Stage Four may start only when:

- required model-ready artifacts exist for TRAIN/VALIDATION/TEST;
- quality checks have no blocking failures;
- leakage checks pass;
- traceability chain is recoverable;
- `stage-three final-report` returns `READY_FOR_STAGE_FOUR`.

If PostgreSQL Catalog is unavailable, `final-report` still writes RU/EN reports but marks readiness as `NOT_READY_FOR_STAGE_FOUR`.

## Related docs

- [../stage-three/README.md](../stage-three/README.md)
- [../stage-three/usage_guide.md](../stage-three/usage_guide.md)
- [../stage-three/stage_three_commands.md](../stage-three/stage_three_commands.md)
- [traceability.md](traceability.md)
- [data_leakage_prevention.md](data_leakage_prevention.md)
