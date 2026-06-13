# Data quality checks

Quality layer реализован в `scripts/stage_two/quality/checkers.py`.

## DuckDB checks

Команда:

```powershell
python manage.py stage-two run-duckdb-checks
```

Проверяет:

- row counts по role/branch, если такие колонки доступны;
- наличие обязательных колонок в `normalized_all`, `features_all`, `model_ready_all`;
- split contamination rule для model-ready;
- schema mismatch summary.

Отчет сохраняется в:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/duckdb_analytics_report.json
```

и регистрируется в `data_quality_reports`.

## DataQualityChecker

`DataQualityChecker` дополнительно проверяет:

- required columns;
- null counts для required columns;
- duplicate keys для `event_uid`/`sample_uid`, когда ключ присутствует;
- допустимые значения role и branch.

Сохранение отчетов выполняется в RU и EN:

```text
PATH_DATA_STORAGE/reports/en/stage-two/quality/quality_report.json
PATH_DATA_STORAGE/reports/ru/stage-two/quality/quality_report.json
```

## Severity

- Успешные проверки получают `INFO`.
- Ошибки quality получают `ERROR`.
- Leakage checks используют `CRITICAL` при провале.

## Catalog registration

Агрегированные результаты пишутся в `data_quality_reports` с:

- `artifact_type`
- `check_group`
- `check_name`
- `status`
- `severity`
- row counters
- mismatch/leakage counters
- `report_path`
- `details_json`
