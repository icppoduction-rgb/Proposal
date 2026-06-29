# Runbook по runtime-ресурсам

Runbook описывает диагностику Stage Two normalization без изменения raw files.

## Быстрый чеклист статуса

```bash
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

## Если storage не готов

Симптомы:

- `PATH_DATA_STORAGE must be configured`;
- отсутствующие директории в readiness report;
- DuckDB views пустые из-за отсутствующих Parquet roots.

Действия:

```bash
export PATH_DATA_STORAGE=/absolute/path/to/stage-two-storage
python manage.py stage-two bootstrap-storage
python -m scripts.stage_two.readiness_check
```

## Если catalog пустой

Симптомы:

- `catalog_counts.dataset_files = 0`;
- `parser-coverage` нечего проверять;
- `mark-ready` не находит files.

Действия:

```bash
export PATH_FOLDER_DATASETS_FILTER=/absolute/path/to/stage-one-filtered-or-sorted-tree
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
```

Проверьте, что input tree содержит `TRAIN`, `VALIDATION`, `TEST`; scanner не активирует произвольные роли.

## Если parser отсутствует

Симптомы:

- `UNSUPPORTED_FORMAT`;
- `parser-coverage` показывает uncovered combination;
- `normalize-format` не создает normalized artifact.

Действия:

1. Проверить `branch/role/source_format` в `dataset_files`.
2. Проверить `parser_registry` после `seed-parser-registry`.
3. Добавить parser class или registry entry.
4. Перезапустить:

```bash
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage <branch>
python manage.py stage-two mark-ready --branch <branch> --role <ROLE> --format <format> --apply
```

## Если normalization падает

Действия:

```bash
python manage.py stage-two normalize-format \
  --branch <branch> \
  --role <ROLE> \
  --format <format> \
  --limit 10 \
  --workers 1
```

После ошибки проверить:

- `parser_runs.status`, counters, error samples;
- `dataset_files.status` и `error_message`;
- parser-specific warnings;
- schema mismatch report;
- размер файла и необходимость `split-large-files`.

Для больших line-based files:

```bash
python manage.py stage-two split-large-files \
  --branch <branch> \
  --role <ROLE> \
  --format <format> \
  --max-part-size-mb 512 \
  --apply \
  --register
```

## Если проверки DuckDB завершились ошибкой

Проверить:

- существуют ли Parquet files под `PATH_DATA_STORAGE/parquet`;
- совпадают ли paths в catalog и на диске;
- есть ли required columns;
- не смешаны ли roles;
- не записаны ли пустые artifacts вместо ошибок parser.

Запуск:

```bash
python manage.py stage-two run-duckdb-checks
```

## Если leakage checks завершились ошибкой

Проверить:

- model-ready `X` не содержит forbidden columns;
- preprocessing artifacts имеют `fitted_on_role = TRAIN`;
- `TEST` не используется в training context;
- unlabeled events не превращены в benign.

Запуск:

```bash
python manage.py stage-two run-leakage-checks
```

CRITICAL leakage report должен блокировать использование artifact.

## Если traceability chain разорвана

Запуск:

```bash
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
python -m scripts.stage_two.readiness_check
```

Проверить links:

```text
model_ready -> feature -> normalized -> parser_run -> dataset_file -> dataset
```

Если `feature_artifact_id` или `normalized_artifact_id` отсутствует, artifact нельзя считать полностью traceable.

## Несовпадение raw hash

Readiness check пересчитывает hashes для `dataset_files.file_path`. Mismatch означает, что raw file изменился после ingestion или catalog указывает не на тот файл.

Действия:

1. Не перезаписывать catalog вручную без audit.
2. Проверить source path и backup.
3. Повторить `catalog-ingest`, если raw tree официально обновлен.
4. Пересобрать downstream artifacts, потому что normalized/features/model-ready могли быть созданы из старого содержимого.
## Performance runbook для текущего железа

Целевое железо:

- Intel Core i7-14700KF.
- 64 GB DDR5 RAM.
- Samsung M.2 SSD 2 TB.
- MSI GeForce RTX 5060 Ti 16 GB.

Raw normalization ориентирована на CPU. GPU по умолчанию не используется для raw parsers; оставляйте GPU для feature/model-ready/training layers, пока нет отдельного parser backend с проверенной корректностью.

### Цель

- Full Stage Two normalization target: `17 GB <= 3 hours`.
- Требуемая скорость: около `5.67 GB/hour`.
- Ожидаемый target для line-based formats на этом железе: `10-20+ GB/hour` после benchmark validation.

### Безопасный порядок запуска

1. Проверить parser coverage и подготовить один точный bucket.
2. Запустить `benchmark-normalization` на 5-10% файлов.
3. Начать с `safe` или `balanced`.
4. Переходить на `fast` только после проверки parser reports, DuckDB checks, leakage checks, RAM, DB connections и SSD write behavior.
5. Использовать `aggressive` только для line-based formats после чистого `fast` run.
6. Full bucket запускать с `--resume`.
7. Запустить post-run gates:

```bash
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

### Примеры команд

Benchmark:

```bash
python manage.py stage-two benchmark-normalization \
  --branch host \
  --role TEST \
  --format txt \
  --limit 10000 \
  --sample-ratio 0.10 \
  --resource-profile fast
```

Line-based full run:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format txt \
  --resource-profile fast \
  --resume
```

PCAP safe run:

```bash
python manage.py stage-two normalize-format \
  --branch dns \
  --role TRAIN \
  --format pcap \
  --resource-profile safe \
  --workers 3 \
  --packet-mode packet-summary \
  --resume
```

BSON safe run:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TEST \
  --format bson \
  --resource-profile safe \
  --workers 3 \
  --batch-size 75000 \
  --resume
```

### Troubleshooting performance runs

| Проблема | Что проверить | Recovery |
| --- | --- | --- |
| PostgreSQL timeout | long transactions, locks, slow catalog writes | уменьшить `--workers`, использовать `safe`, перезапустить с `--resume` |
| too many DB connections | process workers vs DB pool size | ограничить workers до `4-8`, не использовать `aggressive`, проверить worker-local sessions |
| memory pressure | batch size, output part rows, binary formats | уменьшить `--batch-size`, уменьшить `--max-output-part-rows`, split для line-based files |
| SSD throttling | high concurrent writes, temperature, hashing | уменьшить workers, отключить output hashing на итерациях, разделить большие buckets |
| too many small files | scheduler и catalog overhead | использовать bounded execution, группировать exact format, избегать mixed all-branch runs |
| parser errors | parser run reports, error samples, malformed rows | исправить parser/schema handling; не считать malformed rows успешными silently |
| empty DuckDB views | нет Parquet roots или неверный storage path | проверить `PATH_DATA_STORAGE`, artifact paths и `run-duckdb-checks` report |
| leakage critical | forbidden X columns или TEST в training artifacts | остановить training use, проверить leakage report, пересобрать feature/model-ready artifacts |

### Safety rules

- Не изменять raw dataset files.
- Не смешивать `TRAIN`, `VALIDATION`, `TEST`.
- Не использовать `TEST` для training, preprocessing fit, scaler/encoder fit, feature selection или threshold tuning.
- PostgreSQL остается catalog/control plane, Parquet хранит большие данные.
- Labels и path/source/scenario fields не попадают в model-ready X.
- Missing labels не считаются benign.
- Missing timestamps не заменяются current time.
- Traceability сохраняется от raw file до normalized, features и model-ready artifacts.
