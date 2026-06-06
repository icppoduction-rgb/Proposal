# Отчёт по Task7: Analysis of host validation txt dataset files

## Описание задачи
Выполнен анализ `PATH_HOST_DATASETS_FILTER\VALIDATION\txt` на основе `sort-path-host-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_validation_txt_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-validation-txt-summary.json`
- `docs/ru/analysis-dataset/host/validation/txt.md`
- `docs/en/analysis-dataset/host/validation/txt.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task7(Analysis of host validation txt dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task7(Analysis of host validation txt dataset files)_report.md`

## Структура JSON
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `VALIDATION.txt`.

## Логика анализа
Handler берёт равномерную выборку файлов и читает ограниченное число строк на файл streaming-режимом.

## Пример итогового JSON
```json
{
  "format": "txt",
  "role": "VALIDATION",
  "scope": {
    "total_files_count": 6495,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_lines": 30000,
  "unmatched_lines": 0,
  "top_method_names": {
    "read": 2348,
    "munmap": 2325,
    "close": 2319,
    "mmap": 2250,
    "open": 2177,
    "mprotect": 1375,
    "fstat": 1309,
    "newfstatat": 1270
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Результат
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-validation-txt-summary.json`. Итоговый статус: `READY_FOR_FEATURE_EXTRACTION`.
