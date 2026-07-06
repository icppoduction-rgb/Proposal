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

### 5. Optional Host feature extraction

Host path шире DNS MVP и должен запускаться только после отдельного `validate-inputs` для каждой роли:

```powershell
python manage.py stage-three validate-inputs --branch host --role TRAIN
python manage.py stage-three validate-inputs --branch host --role VALIDATION
python manage.py stage-three validate-inputs --branch host --role TEST
```

Если любая Host role возвращает `FAIL`, extraction/model-ready шаги для этой роли запускать нельзя. `WARN` допустим только после явного принятия parser/schema/label рисков из отчета.

Текущие поддержанные Host feature groups:

- `host_syscall`
- `host_process`
- `host_auth`
- `host_file_access`
- `host_metrics`
- `host_logs`

Минимальный Host extraction запуск:

```powershell
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_syscall --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_process --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_auth --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_file_access --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_metrics --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TRAIN --feature-group host_logs --experiment-id exp001-host --resume
```

Для полноценного Host experiment повторить нужные feature groups для `VALIDATION` и `TEST`:

```powershell
python manage.py stage-three extract-features --branch host --role VALIDATION --feature-group host_syscall --experiment-id exp001-host --resume
python manage.py stage-three extract-features --branch host --role TEST --feature-group host_syscall --experiment-id exp001-host --resume
```

Sequence artifacts нужны только если downstream Stage Four будет использовать sequence/DL-модели:

```powershell
python manage.py stage-three build-sequences --branch host --role TRAIN --feature-group host_syscall --experiment-id exp001-host --resume
python manage.py stage-three build-sequences --branch host --role VALIDATION --feature-group host_syscall --experiment-id exp001-host --resume
python manage.py stage-three build-sequences --branch host --role TEST --feature-group host_syscall --experiment-id exp001-host --resume
```

Host ограничения:

- Host `TEST` используется только для final evaluation/inference.
- Большинство Host источников не имеют embedded labels; missing labels должны оставаться `unlabeled`.
- Mixed schemas и большие `txt`/`json`/`bson`/`log` inputs требуют проверки Stage Two parser reports до Stage Three.
- Hybrid/Host-Network correlation не является частью минимального Host path и должен идти отдельным experiment_id.

### 6. Align labels

```powershell
python manage.py stage-three align-labels --branch dns --role TRAIN --label-policy explicit_only --experiment-id exp001 --resume
python manage.py stage-three align-labels --branch dns --role VALIDATION --label-policy explicit_only --experiment-id exp001 --resume
python manage.py stage-three align-labels --branch dns --role TEST --label-policy explicit_only --experiment-id exp001 --resume
```

Для Host использовать отдельный experiment_id:

```powershell
python manage.py stage-three align-labels --branch host --role TRAIN --label-policy explicit_only --experiment-id exp001-host --resume
python manage.py stage-three align-labels --branch host --role VALIDATION --label-policy explicit_only --experiment-id exp001-host --resume
python manage.py stage-three align-labels --branch host --role TEST --label-policy explicit_only --experiment-id exp001-host --resume
```

Labels не должны попадать в model-ready X. Missing labels остаются `unlabeled`, а не превращаются в benign.

### 7. Build model-ready artifacts

```powershell
python manage.py stage-three build-model-ready --experiment-id exp001 --branch dns --target label_binary --preprocessing-profile tree_unscaled --resume
```

Host model-ready artifacts собираются отдельно:

```powershell
python manage.py stage-three build-model-ready --experiment-id exp001-host --branch host --target label_binary --preprocessing-profile tree_unscaled --resume
```

Ожидаемые outputs:

- `X.parquet`
- `y.parquet`
- `metadata.parquet`
- `traceability.parquet`
- `split_index.parquet`
- `preprocessing_metadata.parquet`

### 7.1. DNS supervised 70/30 rebalanced split

Для DNS supervised baseline используется отдельный воспроизводимый split policy
`dns_supervised_70_30_v1`. Он не удаляет raw-файлы физически, сначала выполняет
dry-run audit, затем при `--apply` пишет новый model-ready experiment:

```powershell
python manage.py stage-three rebalance-dns-supervised --experiment-id dns_rebalanced_70_30_v1

python manage.py stage-three rebalance-dns-supervised `
  --experiment-id dns_rebalanced_70_30_v1 `
  --apply `
  --apply-catalog `
  --deactivate-existing-experiment exp001
```

Политика:

- итоговый supervised total: `12,267,021`;
- `TRAIN`: `6,010,841` normal / `2,576,074` attack;
- `VALIDATION`: `1,288,037` normal / `552,016` attack;
- `TEST`: `1,288,037` normal / `552,016` attack;
- текущий битый DNS `TEST/csv` и его chunked downstream artifacts исключаются;
- `VALIDATION/pcap/ens33-dns_amplification_attack.pcap` исключается полностью;
- `VALIDATION/pcap/ens33-dns_amplification_attack__f291ed87a1.pcap` используется только в пределах global target;
- `label_binary=NULL` не включается в supervised split;
- `X.parquet` содержит только DNS lexical feature columns, без labels/source/path/role fields.

Отчет:

```text
reports/ru/stage-three/dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
reports/ru/stage-three/dns_rebalanced_70_30_v1_dns_rebalanced_split_report.md
```

Вердикт: DNS model-ready данные готовы для обучения supervised tabular модели.
Использовать только experiment `dns_rebalanced_70_30_v1`.

Полный model-ready root:

```text
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled
```

Ключевые файлы:

```text
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TRAIN\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TRAIN\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\VALIDATION\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\VALIDATION\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TEST\X.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\TEST\y.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\EXPERIMENTS\split_index.parquet
C:\Users\Public\PythonProjects\storage\parquet\model_ready\dns_rebalanced_70_30_v1\dns\tree_unscaled\EXPERIMENTS\preprocessing_metadata.parquet
```

Проверочные отчеты:

```text
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.md
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\dns_rebalanced_70_30_v1_dns_rebalanced_split_report.json
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task18-stage-three-quality-checks.md
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task18-stage-three-quality-checks.md
C:\Users\Public\PythonProjects\storage\reports\ru\stage-three\Task19-stage-three-leakage-and-traceability-checks.md
C:\Users\Public\PythonProjects\storage\reports\en\stage-three\Task19-stage-three-leakage-and-traceability-checks.md
```

Важно: если сохранять уже существующие `TRAIN` attack rows (`409,076`) и одновременно
держать global target `attack=3,680,106`, из ограничиваемого attack-source в итоговый
supervised split входит `3,271,030` rows. Значение `3,680,106` остается верхней
границей для source, но не количеством, которое можно дополнительно добавить без
нарушения global 70/30 target.

### 8. Run checks

```powershell
python manage.py stage-three run-quality-checks --experiment-id exp001
python manage.py stage-three run-leakage-checks --experiment-id exp001
python manage.py stage-three run-quality-checks --experiment-id dns_rebalanced_70_30_v1
python manage.py stage-three run-leakage-checks --experiment-id dns_rebalanced_70_30_v1
python manage.py stage-three run-quality-checks --experiment-id exp001-host
python manage.py stage-three run-leakage-checks --experiment-id exp001-host
```

Blocking failures должны быть исправлены до Stage Four.
Для `dns_rebalanced_70_30_v1` `run-quality-checks` должен возвращать `PASS`
без `blocking_issues` и без предупреждений по timestamp. `run-leakage-checks` для этого
experiment должен возвращать `PASS`.

### 9. Generate final report

```powershell
python manage.py stage-three final-report --experiment-id exp001
python manage.py stage-three final-report --experiment-id exp001-host
```

Final report сообщает `READY_FOR_STAGE_FOUR` или `NOT_READY_FOR_STAGE_FOUR` и перечисляет explicit gaps.

## Правила безопасности данных

- TEST нельзя использовать для training, fit preprocessing, feature selection или threshold tuning.
- VALIDATION/TEST нельзя балансировать через resampling.
- `label_*`, source/path/parser/raw/metadata/traceability поля нельзя включать в X.
- Stage Three не должен читать raw files как основной источник.
- PostgreSQL используется как catalog/metadata layer; крупные данные остаются в Parquet.
