# Stage Two usage guide

Этот runbook описывает реализованный операционный путь от filtered dataset root до normalized Parquet artifacts.

## Предварительные условия

1. Настройте `.env` или environment variables:

```text
PATH_DATA_STORAGE=<absolute storage root>
PATH_FOLDER_DATASETS=<absolute raw dataset root для Stage One/audit>
PATH_FOLDER_DATASETS_FILTER=<absolute filtered dataset root для Stage Two>
DATABASE_URL=<PostgreSQL SQLAlchemy URL>
```

2. PostgreSQL должен быть доступен по `DATABASE_URL`.
3. Поддерживаемый runtime - Python 3.11.x. На локальной Windows dev-машине используйте `C:\Users\fmark\.conda\envs\proposal2\python.exe` или активируйте `conda activate proposal2`.
4. Для development и CI checks должны быть установлены зависимости из `requirements-dev.txt`; для production/runtime install можно использовать `requirements.txt`.
5. Команды запускаются из корня репозитория.
6. Stage Two smoke-скрипты запускаются как модули: `python -m scripts.stage_two.<module>`.
   Прямой запуск по пути вроде `python scripts/stage_two/parser_smoke.py` не поддерживается, потому что может убрать корень репозитория из `sys.path` и сломать импорты `scripts.*`.

## Рекомендуемый порядок

### 1. Bootstrap storage

```powershell
python manage.py stage-two bootstrap-storage
```

Ожидаемый output:

```text
{
  "service": "stage-two bootstrap-storage",
  "root": "...",
  "created_count": <number>,
  "existing_count": <number>
}
```

Команда idempotent. Она создает directories под `PATH_DATA_STORAGE` для Parquet, reports, DuckDB, logs, config, schemas и temp data.

### 2. Database migrations

```powershell
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python -m alembic -c scripts/db/migrations/alembic.ini current
```

Ожидаемое состояние:

```text
5a38996dff5f (head)
```

### 3. Seed parser registry and schema version

```powershell
python manage.py stage-two seed-parser-registry
```

Output содержит:

```text
"service": "stage-two seed-parser-registry"
"schema_name": "normalized_event"
"schema_version": "v1"
"inserted": <number>
"updated": <number>
```

Команда idempotent и читает `scripts/stage_two/parser_registry/parser_registry_seed.json`.

### 4. Catalog ingest

```powershell
python manage.py stage-two catalog-ingest
```

Что происходит:

- `DatasetFileScanner` сканирует только `PATH_FOLDER_DATASETS_FILTER`.
- Определяются `branch`, `role`, `source_format`, dataset name, file size и SHA-256 hash.
- Заполняются или обновляются `datasets`, `ingestion_runs`, `dataset_files`.
- Raw files не изменяются.
- В Stage Two catalog попадают только роли `TRAIN`, `VALIDATION`, `TEST`. `EXPERIMENTS` игнорируется.

Типовые statuses после ingestion:

| Status | Значение |
| --- | --- |
| `REGISTERED` | Новый файл добавлен в catalog. |
| `CHANGED` | Hash/metadata уже известного файла изменились. |
| `DISCOVERED` | Файл найден и может быть promoted. |
| `EMPTY_FILE` | Файл пустой. |
| `UNSUPPORTED_FORMAT` | Scanner нашел format без active parser coverage. |

`PATH_FOLDER_DATASETS` намеренно не сканируется этой командой. Он остается immutable raw source location и может содержать лишние датасеты, которые не входят в текущий рабочий корпус.

### 5. Parser coverage

```powershell
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage host
python manage.py stage-two parser-coverage dns
```

Колонки output:

```text
branch | role | source_format | files_count | parser_active | parser_class | parser_name | action
```

Ключевые `action` values:

| Action | Значение |
| --- | --- |
| `ready_for_normalization` | Catalog files существуют и active parser доступен. |
| `parser_available_empty_bucket` | Файлов сейчас нет, но registry coverage есть. |
| `add_parser_registry_entry` | В catalog есть format без registry entry. |
| `implement_parser_class` | Registry указывает на class, который не импортируется. |
| `activate_parser_registry_entry` | Registry row есть, но inactive. |

Не запускайте широкую нормализацию, если `catalog_gap_rows` или `missing_parser_rows` не равны нулю.

### 6. Mark ready

Сначала dry-run:

```powershell
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
```

Запись только после проверки counts:

```powershell
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
```

Fallback syntax:

```powershell
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
```

Только эти statuses переводятся в `READY_FOR_PARSING`:

```text
REGISTERED, CHANGED, DISCOVERED
```

Эти statuses не меняются:

```text
EMPTY_FILE, FAILED, PARSED, PARTIALLY_PARSED, SKIPPED
```

### 7. Normalize one format

```powershell
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 100
```

Fallback syntax:

```powershell
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
```

Output содержит selected/processed/normalized counts, parser name/class, per-file status и artifact id, если artifact создан.

### 8. Normalize branch

```powershell
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two normalize-all --branch dns --limit 1000
```

Fallback syntax:

```powershell
python manage.py stage-two normalize-all host:1000
```

`normalize-all` выбирает только `READY_FOR_PARSING` files и группирует работу по `role` и `source_format`.

### 9. Checks

```powershell
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Ожидаемый result:

```text
status: SUCCESS
```

Reports пишутся в `PATH_DATA_STORAGE/reports/en/stage-two/` и `PATH_DATA_STORAGE/reports/ru/stage-two/`.

## Проверка успешного завершения

Для обычного parser workflow:

```powershell
python -m compileall manage.py config.py scripts tests
git diff --check
python -m scripts.db.smoke_check
python manage.py stage-two parser-coverage
python -m scripts.stage_two.parser_smoke
python -m scripts.stage_two.parser_input_smoke
python -m scripts.stage_two.parser_catalog_smoke
python -m scripts.stage_two.cli_operational_smoke
```

Catalog smoke и CLI smoke используют synthetic files и откатывают DB changes.
Не запускайте эти smoke-скрипты через `python scripts/stage_two/*.py`; используйте module form из блока выше.

## Troubleshooting

| Симптом | Вероятная причина | Исправление |
| --- | --- | --- |
| `DATABASE_URL` connection error | PostgreSQL не запущен или URL неверный. | Запустить PostgreSQL и проверить `.env`. |
| `PATH_DATA_STORAGE must be configured` | Storage root пустой. | Задать `PATH_DATA_STORAGE` и запустить `bootstrap-storage`. |
| `parser_active=no` в coverage | Нет registry/class mapping. | Обновить seed, реализовать class, запустить `seed-parser-registry`. |
| `selected=0` в `mark-ready` | Нет matching rows или statuses не eligible. | Проверить `parser-coverage` и `dataset_files.status`. |
| `selected=0` в `normalize-format` | Matching files не `READY_FOR_PARSING`. | Запустить `mark-ready --apply` для exact branch/role/format. |
| `PARTIAL_SUCCESS` | Часть rows failed, часть parsed. | Смотреть parser run reports в `reports/*/stage-two/parser/`. |
| DuckDB report fails on missing Parquet | Нет normalized artifacts для scope. | Сначала нормализовать небольшой batch. |

## Production safety notes

- Не редактировать raw datasets, чтобы parser "заработал".
- Не использовать `EXPERIMENTS` в Stage Two командах; рабочие роли: `TRAIN`, `VALIDATION`, `TEST`.
- Не хранить raw packet payloads, BSON streams или full raw logs в PostgreSQL metadata.
- Не переводить целые branches в ready без просмотра `parser-coverage`.
- Не считать synthetic smoke tests подтверждением full-corpus readiness.
