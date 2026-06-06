# Отчёт по Task3: Analysis of host validation json dataset files

## Описание задачи
Выполнен анализ `PATH_HOST_DATASETS_FILTER\VALIDATION\json` на основе `sort-path-host-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_validation_json_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-validation-json-summary.json`
- `docs/ru/analysis-dataset/host/validation/json.md`
- `docs/en/analysis-dataset/host/validation/json.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task3(Analysis of host validation json dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task3(Analysis of host validation json dataset files)_report.md`

## Структура JSON
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `VALIDATION.json`.

## Логика группировки путей
Handler берёт равномерную выборку JSON-файлов и читает ограниченное число JSON Lines записей на файл.

## Пример итогового JSON
```json
{
  "format": "json",
  "role": "VALIDATION",
  "scope": {
    "total_files_count": 130,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_records": 19930,
  "event_ids": {
    "10": 5590,
    "7": 2793,
    "12": 2404,
    "13": 1055,
    "4658": 989,
    "5156": 867,
    "800": 609,
    "4103": 553,
    "4656": 531,
    "5158": 510,
    "4690": 469,
    "5447": 436,
    "4663": 353,
    "23": 320,
    "4703": 278,
    "4799": 195,
    "3": 191,
    "9": 178,
    "11": 140,
    "4673": 135
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Результат
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-validation-json-summary.json`. Итоговый статус: `READY_FOR_FEATURE_EXTRACTION`.
