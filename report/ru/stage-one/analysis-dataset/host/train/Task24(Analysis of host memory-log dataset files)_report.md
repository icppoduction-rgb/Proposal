# Отчёт: Task24 (Analysis of host memory-log dataset files)

## Описание задачи
Переделан этап анализа `TRAIN/memory.log` с генерацией RU/EN-документации и обновлением README индексов.

## Какие файлы были добавлены или изменены
- `scripts/handlers/analyze_host_memory_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/memory.log.md`
- `docs/en/analysis-dataset/host/memory.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task24(Analysis of host memory-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task24(Analysis of host memory-log dataset files)_report.md`
- `temp_data/analysis-host-memory-log-summary.json`

## Описание структуры JSON
- json_document: `0`
- json_lines: `12`
- unparsed: `0`

## Логика группировки путей
1. Загружен `sort-path-host-file.json`.
2. Выбран bucket `TRAIN -> memory.log`.
3. Применена равномерная выборка файлов по всему диапазону имен.
4. Для каждого sample-файла выполнен анализ как `json document`, затем fallback в `json-lines`.

## Пример итогового JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "memory.log",
    "total_files_count": 12,
    "sampled_files_count": 12,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000,
    "max_bytes_per_file": 2097152
  },
  "technical": {
    "schema_counts": {
      "json_document": 0,
      "json_lines": 12,
      "raw_text": 0,
      "unparsed": 0
    }
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-memory-log-summary.json`
