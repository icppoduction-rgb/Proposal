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
