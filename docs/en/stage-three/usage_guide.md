# Stage Three Usage Guide

## Prerequisites

Before Stage Three, Stage Two artifacts must be ready:

- normalized Parquet artifacts are registered in the PostgreSQL Catalog;
- parser runs have no blocking failures for the target branch/role;
- Stage Two quality/leakage/traceability checks passed;
- `PATH_DATA_STORAGE` and `DATABASE_URL` are configured in `.env`.

Environment smoke command:

```powershell
cmd /c "C:\ProgramData\Anaconda3\condabin\conda.bat activate C:\Users\fmark\.conda\envs\proposal && python manage.py stage-three --help"
```

## Execution Flow

### 1. Validate Stage Two inputs

```powershell
python manage.py stage-three validate-inputs --branch dns --role TRAIN
python manage.py stage-three validate-inputs --branch dns --role VALIDATION
python manage.py stage-three validate-inputs --branch dns --role TEST
```

If the command returns `FAIL`, do not run downstream Stage Three commands for that branch.

### 2. Build feature catalog

```powershell
python manage.py stage-three build-feature-catalog
```

The command validates `scripts/stage_three/feature_catalog/feature_catalog.yml` and writes a normalized JSON snapshot.

### 3. Probe runtime backend

```powershell
python manage.py stage-three probe-runtime-backend --backend auto
```

Default policy: CPU-first, streaming-first. GPU is used only after capability and correctness checks.

### 4. Extract DNS MVP features

```powershell
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_entropy --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_temporal --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role VALIDATION --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TEST --feature-group dns_lexical --experiment-id exp001 --resume
```

For production, repeat extraction for all required feature groups and roles.

### 5. Align labels

```powershell
python manage.py stage-three align-labels --branch dns --role TRAIN --label-policy explicit_only --experiment-id exp001 --resume
python manage.py stage-three align-labels --branch dns --role VALIDATION --label-policy explicit_only --experiment-id exp001 --resume
python manage.py stage-three align-labels --branch dns --role TEST --label-policy explicit_only --experiment-id exp001 --resume
```

Labels must not enter model-ready X. Missing labels remain `unlabeled`; they are not converted to benign.

### 6. Build model-ready artifacts

```powershell
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
```

Expected outputs:

- `X.parquet`
- `y.parquet`
- `metadata.parquet`
- `traceability.parquet`
- `split_index.parquet`
- `preprocessing_metadata.parquet`

### 6.1. DNS supervised 70/30 rebalanced split

For the DNS supervised baseline, use the reproducible split policy
`dns_supervised_70_30_v1`. It writes the active model-ready experiment
`dns_rebalanced_70_30_v1`.

```powershell
python manage.py stage-three rebalance-dns-supervised --experiment-id dns_rebalanced_70_30_v1

python manage.py stage-three rebalance-dns-supervised `
  --experiment-id dns_rebalanced_70_30_v1 `
  --apply `
  --apply-catalog `
  --deactivate-existing-experiment exp001
```

Training-readiness verdict:

- DNS model-ready data is ready for supervised tabular model training.
- Use only experiment `dns_rebalanced_70_30_v1`.
- `TRAIN`: `6,010,841` normal / `2,576,074` attack.
- `VALIDATION`: `1,288,037` normal / `552,016` attack.
- `TEST`: `1,288,037` normal / `552,016` attack.
- `label_binary=NULL` is absent from the final supervised split.
- Duplicate samples across `TRAIN` / `VALIDATION` / `TEST`: `0`.
- `TEST` must not be used for training, preprocessing fit, feature selection, or threshold tuning.

Model-ready root:

```text
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled
```

Primary reports:

```text
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.md
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task18-stage-three-quality-checks.md
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task19-stage-three-leakage-and-traceability-checks.md
```

### 7. Run checks

```powershell
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
python manage.py stage-three run-quality-checks --experiment-id dns_rebalanced_70_30_v1
python manage.py stage-three run-leakage-checks --experiment-id dns_rebalanced_70_30_v1
```

Blocking failures must be fixed before Stage Four.
For `dns_rebalanced_70_30_v1`, `run-quality-checks` must return `PASS` with no
`blocking_issues` and no timestamp warnings.
`run-leakage-checks` for this experiment must return `PASS`.

### 8. Generate final report

```powershell
python manage.py stage-three final-report --experiment-id exp001
```

The final report states `READY_FOR_STAGE_FOUR` or `NOT_READY_FOR_STAGE_FOUR` and lists explicit gaps.

## Data Safety Rules

- TEST must not be used for training, preprocessing fit, feature selection, or threshold tuning.
- VALIDATION/TEST must not be balanced through resampling.
- `label_*`, source/path/parser/raw/metadata/traceability fields must not enter X.
- Stage Three must not read raw files as the primary input.
- PostgreSQL is a catalog/metadata layer; large data stays in Parquet.
