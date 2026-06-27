# Проверки качества данных

Код проверок:

- `scripts/stage_two/duckdb/service.py`;
- `scripts/stage_two/quality/checks.py`;
- `scripts/stage_two/quality/checkers.py`.

## Аналитические проверки DuckDB

Команда:

```bash
python manage.py stage-two run-duckdb-checks
```

Проверки:

| Проверка | Область | Условие отказа |
|---|---|---|
| `row_counts_*` | normalized/features/model-ready views | не падает; формирует counts |
| `missing_required_columns_*` | каждое view | отсутствуют required columns |
| `split_contamination` | `model_ready_all` | TEST rows присутствуют в TRAIN model-ready artifacts |
| `schema_mismatch` | все views | mismatch required columns |

Отчет:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/duckdb_analytics_report.json
```

Регистрация в catalog:

- table: `data_quality_reports`;
- `check_group='duckdb'`;
- severity `ERROR`, если есть failed checks, иначе `INFO`.

## DataQualityChecker

Класс: `DataQualityChecker`.

Проверки:

| Группа проверок | Детали |
|---|---|
| Обязательные columns | использует DuckDB `REQUIRED_COLUMNS` |
| Null counts | считает nulls в required columns, присутствующих во view |
| Duplicate keys | `event_uid` для normalized, `sample_uid` для features/model-ready |
| Role/branch domains | валидирует значения `role`, `dataset_role`, `branch` |

Выходные отчеты:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/quality_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/quality/quality_report.json
```

Опциональная регистрация в catalog выполняется через `DataQualityRepository`.

Severity:

- successful checks: `INFO`;
- failed data quality checks: `ERROR`.

## LeakageChecker

Подробности leakage описаны в [data_leakage_prevention.md](data_leakage_prevention.md). Checker пишет:

```text
PATH_DATA_STORAGE/reports/en/stage-two/leakage/leakage_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/leakage/leakage_report.json
```

Severity для failed leakage report: `CRITICAL`.

## Контракт отчета

`QualityCheckResult`:

```text
check_name
status
severity
rows_total
rows_failed
details
```

`QualityReportResult`:

```text
check_group
status
severity
report_paths
checks
```

## Критические нарушения

CRITICAL считаются:

- label/source/leakage columns с non-null values в model-ready X files;
- TEST rows в TRAIN model-ready artifacts;
- preprocessing artifact с fit на role, отличной от TRAIN.

Эти нарушения должны блокировать использование model-ready artifact для training.
