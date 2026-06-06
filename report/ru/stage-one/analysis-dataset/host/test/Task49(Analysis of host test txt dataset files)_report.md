# Отчёт по Task49: Analysis of host test txt dataset files

## Описание задачи
Выполнен анализ `PATH_HOST_DATASETS_FILTER\TEST\txt` на основе `sort-path-host-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_test_txt_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-test-txt-summary.json`
- `docs/ru/analysis-dataset/host/test/txt.md`
- `docs/en/analysis-dataset/host/test/txt.md`
- `docs/ru/analysis-dataset/host/test/README.md`
- `docs/en/analysis-dataset/host/test/README.md`
- `report/ru/stage-one/analysis-dataset/host/test/Task49(Analysis of host test txt dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/test/Task49(Analysis of host test txt dataset files)_report.md`

## Структура JSON
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `TEST.txt`.

## Логика группировки путей
Handler берёт равномерную выборку по огромному списку TXT-файлов и читает ограниченное число строк на файл.

## Пример итогового JSON
```json
{
  "format": "txt",
  "role": "TEST",
  "scope": {
    "total_files_count": 274419,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "parsed_lines": 6901,
  "top_method_names": {
    "NtSetEventBoostPriority": 1000,
    "ZwAllocateVirtualMemory": 1000,
    "ZwQueryInformationToken": 1000,
    "ZwWaitForSingleObject": 1000,
    "ZwReplyWaitReceivePort": 682
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Результат
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-test-txt-summary.json`. Итоговый статус: `READY_FOR_FEATURE_EXTRACTION`.
