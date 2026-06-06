# Отчёт по Task50: Analysis of host test wls_day dataset files

## Описание задачи
Выполнен анализ `PATH_HOST_DATASETS_FILTER\TEST\wls_day` на основе `sort-path-host-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_test_wls_day_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-wls-day-summary.json`
- `docs/ru/analysis-dataset/host/test/wls_day.md`
- `docs/en/analysis-dataset/host/test/wls_day.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task50(Analysis of host test wls_day dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task50(Analysis of host test wls_day dataset files)_report.md`

## Структура JSON
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `TEST.wls_day`.

## Логика группировки путей
Handler анализирует все 3 файла и читает ограниченное число JSON Lines записей на файл.

## Пример итогового JSON
```json
{
  "format": "wls_day",
  "role": "TEST",
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
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-wls-day-summary.json`. Итоговый статус: `READY_FOR_FEATURE_EXTRACTION`.
