# Stage Two: нормализация данных

Stage Two переводит сырые файлы датасетов в воспроизводимую цепочку артефактов:

```text
raw dataset file -> PostgreSQL catalog -> normalized Parquet -> feature Parquet -> model-ready artifacts
```

PostgreSQL хранит только каталог, статусы, метаданные, связи и отчеты. Большие normalized, features и model-ready данные хранятся в Parquet под `PATH_DATA_STORAGE`. DuckDB используется для SQL-проверок поверх Parquet.

## Основные команды

```powershell
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two normalize-dns
python manage.py stage-two normalize-host
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Команды нормализации обрабатывают файлы со статусом `READY_FOR_PARSING`. Допускается необязательный лимит:

```powershell
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
```

## Разделы

- [Архитектура хранилища](storage_architecture.md)
- [PostgreSQL catalog schema](postgresql_catalog_schema.md)
- [Normalized event schema](normalized_event_schema.md)
- [Parser strategy](parser_strategy.md)
- [Parquet и DuckDB artifacts](parquet_duckdb_artifacts.md)
- [Data quality checks](data_quality_checks.md)
- [Data leakage prevention](data_leakage_prevention.md)

## Ключевые инварианты

- TRAIN, VALIDATION и TEST не смешиваются в каталогах, Parquet-путях и model-ready артефактах.
- TEST не используется для fit scaler, encoder, imputer, feature selector, threshold или модели.
- Отсутствующие поля сохраняются как `NULL`/Parquet null, а не заполняются фиктивными значениями.
- Traceability должна сохранять путь от `model_ready_artifacts` к `feature_artifacts`, `normalized_artifacts`, `parser_runs`, `dataset_files` и `datasets`.
- Labels отделяются от X-признаков; leakage-поля запрещены в X.
