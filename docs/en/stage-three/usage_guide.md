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

### 7. Run checks

```powershell
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
```

Blocking failures must be fixed before Stage Four.

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
