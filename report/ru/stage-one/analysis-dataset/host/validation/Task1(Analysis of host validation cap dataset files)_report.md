# Отчёт по Task1: Analysis of host validation cap dataset files

## Описание задачи
Выполнен анализ `PATH_HOST_DATASETS_FILTER\VALIDATION\cap` на основе `sort-path-host-file.json`. Исходные датасеты не изменялись, обучение моделей не выполнялось.

## Добавленные или изменённые файлы
- `scripts/handlers/analyze_host_validation_cap_dataset_handler.py`
- `manage.py`
- `temp_data/analysis-host-validation-cap-summary.json`
- `docs/ru/analysis-dataset/host/validation/cap.md`
- `docs/en/analysis-dataset/host/validation/cap.md`
- `docs/ru/analysis-dataset/host/validation/README.md`
- `docs/en/analysis-dataset/host/validation/README.md`
- `report/ru/stage-one/analysis-dataset/host/validation/Task1(Analysis of host validation cap dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/validation/Task1(Analysis of host validation cap dataset files)_report.md`

## Структура JSON
`sort-path-host-file.json`: `role -> format -> list[path]`; bucket: `VALIDATION.cap`.

## Логика группировки путей
Handler сортирует пути, берёт равномерную выборку и читает только pcap headers + ограниченное число packets.

## Пример итогового JSON
```json
{
  "format": "cap",
  "role": "VALIDATION",
  "scope": {
    "total_files_count": 44,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_packets_per_file": 500
  },
  "parsed_packets": 10258,
  "ip_protocols": {
    "6": 10148,
    "17": 110
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

## Результат
Создан summary `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-validation-cap-summary.json`. Итоговый статус: `NEEDS_CUSTOM_PARSER`.
