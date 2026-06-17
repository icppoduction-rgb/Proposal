# Stage Two: нормализация данных

Stage Two переводит сырые файлы датасетов в воспроизводимую цепочку артефактов:

```text
raw dataset file -> PostgreSQL catalog -> normalized Parquet -> feature Parquet -> model-ready artifacts
```

PostgreSQL хранит catalog metadata, statuses, relationships, parser runs, artifact records и reports. Большие normalized, feature и model-ready данные хранятся в Parquet под `PATH_DATA_STORAGE`. DuckDB используется для SQL-проверок поверх Parquet.

## Основные команды

```powershell
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two parser-coverage host
python manage.py stage-two parser-coverage dns
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Parser workflow

Сначала проверьте coverage, не меняя статусы файлов:

```powershell
python manage.py stage-two parser-coverage
```

Переведите файлы в ready. Dry-run является безопасным режимом по умолчанию; для записи нужен `--apply`:

```powershell
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --dry-run
python manage.py stage-two mark-ready --branch host --role TRAIN --format auth.log --apply
```

Нормализация одного формата:

```powershell
python manage.py stage-two normalize-format --branch host --role TRAIN --format auth.log --limit 100
python manage.py stage-two normalize-format --branch dns --role VALIDATION --format pcap --limit 100
```

Нормализация всех ready-файлов одной ветки контролируемыми batch по role/format:

```powershell
python manage.py stage-two normalize-all --branch host --limit 1000
python manage.py stage-two normalize-all --branch dns --limit 1000
```

Backward-compatible aliases остаются доступны:

```powershell
python manage.py stage-two normalize-host 10
python manage.py stage-two normalize-dns 10
```

Fallback argument forms также поддерживаются:

```powershell
python manage.py stage-two mark-ready dry-run:host:TRAIN:auth.log
python manage.py stage-two mark-ready apply:host:TRAIN:auth.log
python manage.py stage-two normalize-format host:TRAIN:auth.log:100
python manage.py stage-two normalize-all host:1000
```

## Генерируемые parser reports

Coverage reports пишутся в:

- `PATH_DATA_STORAGE/reports/en/stage-two/parser/parser_coverage_matrix.md`
- `PATH_DATA_STORAGE/reports/ru/stage-two/parser/parser_coverage_matrix.md`

Per-run parser и normalization diagnostics пишутся в:

- `PATH_DATA_STORAGE/reports/en/stage-two/parser/`
- `PATH_DATA_STORAGE/reports/ru/stage-two/parser/`
- `PATH_DATA_STORAGE/reports/en/stage-two/normalization/`
- `PATH_DATA_STORAGE/reports/ru/stage-two/normalization/`

## Разделы

- [Архитектура хранилища](storage_architecture.md)
- [PostgreSQL catalog schema](postgresql_catalog_schema.md)
- [Normalized event schema](normalized_event_schema.md)
- [Parser strategy](parser_strategy.md)
- [Parquet и DuckDB artifacts](parquet_duckdb_artifacts.md)
- [Data quality checks](data_quality_checks.md)
- [Data leakage prevention](data_leakage_prevention.md)

## Ключевые инварианты

- TRAIN, VALIDATION и TEST не смешиваются в catalog rows, Parquet paths и model-ready artifacts.
- TEST никогда не используется для fit scalers, encoders, imputers, feature selectors, thresholds или models.
- `catalog-ingest` не переводит файлы в `READY_FOR_PARSING` автоматически; `mark-ready` является явным operational gate.
- Normalization обрабатывает только файлы `READY_FOR_PARSING`, если команда явно не документирует другое поведение.
- Отсутствующие source fields сохраняются как `NULL`/Parquet null, а не заполняются синтетическими значениями.
- Traceability должна сохранять путь model-ready -> feature -> normalized -> parser run -> raw file -> dataset.
- Labels отделяются от X features; leakage columns запрещены в X.
