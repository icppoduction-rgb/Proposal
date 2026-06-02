# Отчёт: Task11 (Analysis of host json dataset files)

## Описание задачи
Переделан этап анализа `TRAIN/json` с генерацией RU/EN-документации и обновлением README индексов.

## Какие файлы были добавлены или изменены
- `scripts/handlers/analyze_host_json_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/json.md`
- `docs/en/analysis-dataset/host/json.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task11(Analysis of host json dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task11(Analysis of host json dataset files)_report.md`
- `temp_data/analysis-host-json-summary.json`

## Описание структуры JSON
- json_document: `29`
- json_lines: `1`
- unparsed: `0`

## Логика группировки путей
1. Загружен `sort-path-host-file.json`.
2. Выбран bucket `TRAIN -> json`.
3. Применена равномерная выборка файлов по всему диапазону имен.
4. Для каждого sample-файла выполнен анализ как `json document`, затем fallback в `json-lines`.

## Пример итогового JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "json",
    "total_files_count": 219,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000,
    "max_bytes_per_file": 2097152
  },
  "technical": {
    "schema_counts": {
      "json_document": 29,
      "json_lines": 1,
      "unparsed": 0
    }
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-json-summary.json`
