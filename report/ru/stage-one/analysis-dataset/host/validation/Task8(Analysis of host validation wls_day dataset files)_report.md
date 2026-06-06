# Отчёт по Task8: Analysis of host validation wls_day dataset files

## Описание задачи
Выполнен анализ `PATH_HOST_DATASETS_FILTER\VALIDATION\wls_day` на основе `sort-path-host-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_validation_wls_day_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-validation-wls-day-summary.json`
- `docs/ru/analysis-dataset/host/validation/wls_day.md`
- `docs/en/analysis-dataset/host/validation/wls_day.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task8(Analysis of host validation wls_day dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task8(Analysis of host validation wls_day dataset files)_report.md`

## Структура JSON
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `VALIDATION.wls_day`.

## Логика анализа
Handler анализирует все 3 файла и читает ограниченное число JSON Lines записей на файл.

## Пример итогового JSON
```json
{
  "format": "wls_day",
  "role": "VALIDATION",
  "scope": {
    "total_files_count": 3,
    "sampled_files_count": 3,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_records": 3000,
  "event_ids": {
    "4688": 1474,
    "4624": 609,
    "4672": 375,
    "4634": 234,
    "4776": 126,
    "4769": 101,
    "4768": 47,
    "4648": 31,
    "4625": 3
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Результат
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-validation-wls-day-summary.json`. Итоговый статус: `READY_FOR_FEATURE_EXTRACTION`.
