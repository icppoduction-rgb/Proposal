# Stage Three

Stage Three converts Stage Two normalized Parquet outputs into split-safe, leakage-safe, traceable model-ready artifacts for Stage Four.

Main data line:

```text
raw -> normalized -> features -> model-ready -> training/evaluation
```

Stage Three owns only:

```text
normalized -> features -> model-ready
```

RF/XGBoost/CNN/LSTM training, hyperparameter search, threshold tuning, SHAP/XAI, and final experimental evaluation belong to Stage Four.

## Documents

- [usage_guide.md](usage_guide.md) - Stage Three execution flow.
- [stage_three_commands.md](stage_three_commands.md) - CLI command reference.
- [performance_tuning.md](performance_tuning.md) - runtime profile, RAM/GPU policy, and safe performance settings.

## Minimal DNS MVP Path

1. Validate Stage Two readiness for DNS TRAIN/VALIDATION/TEST.
2. Build and validate the feature catalog.
3. Extract DNS feature groups: `dns_lexical`, `dns_entropy`, `dns_temporal`.
4. Build `tree_unscaled` model-ready artifacts for `label_binary`.
5. When needed, build the reproducible DNS supervised 70/30 split with `rebalance-dns-supervised`.
6. Run quality checks.
7. Run leakage and traceability checks.
8. Generate the final report.
9. Move to Stage Four only when the final report says `READY_FOR_STAGE_FOUR`.

## Production Path

After DNS MVP, expand Stage Three to Host/Network/Hybrid:

- add and run Host/Network feature groups;
- enable sequence artifacts when CNN/LSTM/LSTM-like models need them;
- use separate preprocessing profiles for tree/DL/linear models;
- run quality/leakage/traceability checks for every production `experiment_id`;
- never mix TRAIN, VALIDATION, and TEST;
- never fit imputers, scalers, or encoders on VALIDATION or TEST.

## Final Report

Command:

```powershell
python manage.py stage-three final-report --experiment-id <id>
```

Reports are written to:

- `C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task20-stage-three-final-report-and-documentation.md`
- `C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task20-stage-three-final-report-and-documentation.md`
