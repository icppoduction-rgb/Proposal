# Отчёт по Task47: Analysis of host test log dataset files

## Описание задачи
Выполнен анализ `PATH_HOST_DATASETS_FILTER\TEST\log` на основе `sort-path-host-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_test_log_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-log-summary.json`
- `docs/ru/analysis-dataset/host/test/log.md`
- `docs/en/analysis-dataset/host/test/log.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task47(Analysis of host test log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task47(Analysis of host test log dataset files)_report.md`

## Структура JSON
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `TEST.log`.

## Логика группировки путей
Handler сортирует пути, берёт равномерную выборку до 30 файлов и читает до 1000 строк на файл.

## Пример итогового JSON
```json
{
  "format": "log",
  "role": "TEST",
  "scope": {
    "total_files_count": 4086,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_lines": 4834,
  "levels": {
    "DEBUG": 3405,
    "INFO": 1242,
    "WARNING": 171,
    "ERROR": 16
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Результат
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-log-summary.json`. Итоговый статус: `READY_FOR_FEATURE_EXTRACTION`.
