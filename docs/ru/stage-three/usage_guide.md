# Stage Three Usage Guide

## Предусловия

Перед Stage Three должны быть готовы Stage Two artifacts:

- normalized Parquet artifacts зарегистрированы в PostgreSQL Catalog;
- parser runs завершены без blocking failures для нужных branch/role;
- Stage Two quality/leakage/traceability checks пройдены;
- `PATH_DATA_STORAGE` и `DATABASE_URL` заданы в `.env`.

Рабочее окружение:

```powershell
cmd /c "C:\ProgramData\Anaconda3\condabin\conda.bat activate C:\Users\fmark\.conda\envs\proposal && python manage.py stage-three --help"
```

## Последовательность запуска

### 1. Validate Stage Two inputs

```powershell
python manage.py stage-three validate-inputs --branch dns --role TRAIN
python manage.py stage-three validate-inputs --branch dns --role VALIDATION
python manage.py stage-three validate-inputs --branch dns --role TEST
```

Если команда возвращает `FAIL`, downstream-команды Stage Three для этой ветки запускать нельзя.

### 2. Build feature catalog

```powershell
python manage.py stage-three build-feature-catalog
```

Команда валидирует `scripts/stage_three/feature_catalog/feature_catalog.yml` и пишет normalized JSON snapshot.

### 3. Probe runtime backend

```powershell
python manage.py stage-three probe-runtime-backend --backend auto
```

Default policy: CPU-first, streaming-first. GPU используется только после capability/correctness checks.

### 4. Extract DNS MVP features

```powershell
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_entropy --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TRAIN --feature-group dns_temporal --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role VALIDATION --feature-group dns_lexical --experiment-id exp001 --resume
python manage.py stage-three extract-features --branch dns --role TEST --feature-group dns_lexical --experiment-id exp001 --resume
```

Для production повторить extraction для всех нужных feature groups и roles.

### 5. Align labels

```powershell
python manage.py stage-three align-labels --branch dns --role TRAIN --label-policy explicit_only --experiment-id exp001 --resume
python manage.py stage-three align-labels --branch dns --role VALIDATION --label-policy explicit_only --experiment-id exp001 --resume
python manage.py stage-three align-labels --branch dns --role TEST --label-policy explicit_only --experiment-id exp001 --resume
```

Labels не должны попадать в model-ready X. Missing labels остаются `unlabeled`, а не превращаются в benign.

### 6. Build model-ready artifacts

```powershell
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
```

Ожидаемые outputs:

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

Blocking failures должны быть исправлены до Stage Four.

### 8. Generate final report

```powershell
python manage.py stage-three final-report --experiment-id exp001
```

Final report сообщает `READY_FOR_STAGE_FOUR` или `NOT_READY_FOR_STAGE_FOUR` и перечисляет explicit gaps.

## Правила безопасности данных

- TEST нельзя использовать для training, fit preprocessing, feature selection или threshold tuning.
- VALIDATION/TEST нельзя балансировать через resampling.
- `label_*`, source/path/parser/raw/metadata/traceability поля нельзя включать в X.
- Stage Three не должен читать raw files как основной источник.
- PostgreSQL используется как catalog/metadata layer; крупные данные остаются в Parquet.
