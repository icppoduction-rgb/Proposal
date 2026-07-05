# Проверки качества данных

Stage Two использует два уровня проверок:

1. DuckDB analytics checks поверх Parquet views.
2. `DataQualityChecker`/`LeakageChecker` с регистрацией результатов в `data_quality_reports`.

## DuckDB analytics

Команда:

```bash
python manage.py stage-two run-duckdb-checks
```

Runtime-защита:

- команда применяет bounded DuckDB settings: `memory_limit`, `threads`, `temp_directory`, `max_temp_directory_size`;
- значения по умолчанию: `STAGE_TWO_DUCKDB_MEMORY_LIMIT=32GB`, `STAGE_TWO_DUCKDB_THREADS=2`, `STAGE_TWO_DUCKDB_MAX_TEMP_DIRECTORY_SIZE=100GB`;
- spill directory по умолчанию: `PATH_DATA_STORAGE/temp_data/duckdb`;
- для больших Parquet layers команда не создает единый DuckDB view поверх всех файлов; row counts и schema checks считаются потоково по Parquet metadata, а data-level checks выполняются chunked;
- CLI показывает progress bar по подготовке слоев, проверкам, сохранению report и регистрации в catalog.

Код:

```text
scripts/stage_two/duckdb/service.py
```

Проверяет:

- созданы ли views `normalized_all`, `features_all`, `model_ready_all`;
- row counts по Parquet layers;
- наличие required columns;
- split contamination;
- schema mismatch.

Report:

```text
reports/en/stage-two/quality/duckdb_analytics_report.json
```

После регистрации в catalog создается запись `data_quality_reports` с `check_group` для DuckDB/quality diagnostics.

## DataQualityChecker

Код:

```text
scripts/stage_two/quality/checkers.py
```

`DataQualityChecker` читает DuckDB views и проверяет:

| Проверка | Цель |
| --- | --- |
| Required columns | Контрактные колонки присутствуют в views. |
| Null counts | Видимость пустых значений в критичных columns. |
| Duplicate keys | Дубликаты ключевых event/sample identifiers. |
| Role domain | Значения role/dataset_role ограничены `TRAIN`, `VALIDATION`, `TEST`. |
| Branch domain | Значения branch ограничены catalog constants. |

Reports пишутся в RU/EN report roots и могут регистрироваться через `DataQualityRepository`.

## Уровни severity

| Severity | Значение |
| --- | --- |
| `INFO` | Диагностическая информация. |
| `WARNING` | Нежелательное состояние, которое не всегда блокирует pipeline. |
| `ERROR` | Нарушение контракта или качества данных. |
| `CRITICAL` | Нарушение, которое может привести к leakage, смешиванию splits или недостоверному model-ready artifact. |

## Связь с leakage checks

`LeakageChecker` находится в том же модуле, но описан отдельно в [data_leakage_prevention.md](data_leakage_prevention.md). Его CRITICAL results также регистрируются в `data_quality_reports`, обычно с `check_group = "leakage"`.

## Readiness check

```bash
python -m scripts.stage_two.readiness_check
```

Команда выводит progress bar в stderr и JSON result в stdout. Проверка raw file hashes выполняется потоково по колонкам `dataset_files.id/file_path/file_hash_sha256`, без загрузки ORM-объектов всей таблицы в память.

Runtime-настройки для hash scan:

- `STAGE_TWO_READINESS_DB_YIELD_PER` - сколько catalog rows получать за один streaming batch, default `1000`;
- `STAGE_TWO_READINESS_HASH_CHUNK_BYTES` - размер блока чтения raw file при SHA-256, default `1048576` bytes.

Readiness проверяет, что:

- миграции применены;
- storage paths существуют;
- catalog содержит datasets/files/parser_registry/schema_versions/artifacts/reports;
- parser coverage не имеет uncovered combinations;
- normalized artifacts есть и не failed;
- feature/model-ready artifacts связаны с upstream artifacts;
- quality/leakage reports существуют;
- traceability chain восстанавливается;
- raw file hashes совпадают с catalog.

Readiness report сохраняется в:

```text
reports/en/stage-two/stage_two_readiness_report.md
reports/ru/stage-two/stage_two_readiness_report.md
reports/en/stage-two/stage_two_readiness_report.json
```

## Что считается блокирующим

Блокирующие сценарии:

- `TEST` найден в preprocessing fit/training context;
- label/source fields присутствуют в model-ready `X`;
- отсутствует обязательная traceability связь;
- raw file hash не совпадает с catalog;
- parser coverage отсутствует для files, которые должны нормализоваться;
- role contamination между `TRAIN`, `VALIDATION`, `TEST`.

Такие нарушения нужно исправлять до использования artifacts в ML experiments.
