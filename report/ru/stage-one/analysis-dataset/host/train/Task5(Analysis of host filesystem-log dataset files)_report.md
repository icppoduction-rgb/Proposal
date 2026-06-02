# Отчёт: Task5 (Analysis of host filesystem-log dataset files)

## Описание задачи
Реализован отдельный этап анализа формата `TRAIN/filesystem.log` на основе `temp_data/sort-path-host-file.json` с генерацией документации на RU/EN.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_filesystem_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/filesystem.log.md`
- `docs/en/analysis-dataset/host/filesystem.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task5(Analysis of host filesystem-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task5(Analysis of host filesystem-log dataset files)_report.md`
- `temp_data/analysis-host-filesystem-log-summary.json`

## Описание структуры JSON
- top-level keys: ecs, agent, tags, host, @version, system, @timestamp, service, event, metricset
- dataset: `system.filesystem`
- вложенные поля: `system.filesystem.mount_point/type/device_name/used/total/free/available`.

## Логика группировки путей
1. Считывается `sort-path-host-file.json`.
2. Выбирается bucket: `TRAIN -> filesystem.log`.
3. Параллельно читается `sort-path-dns-file.json` для валидации контекста DNS/Host без смешивания данных.
4. Для анализа берётся ограниченный sample файлов и строк.

## Пример итогового JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "filesystem.log",
    "total_files_count": 12,
    "sampled_files_count": 12,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "filesystem.log",
    "dns_formats_detected_count": 3
  },
  "final_status": "READY_FOR_FEATURE_EXTRACTION"
}
```

## Результат
- Всего файлов формата: `12`.
- Sample-файлов проанализировано: `12`.
- Итоговый статус: `READY_FOR_FEATURE_EXTRACTION`.

## Артефакты
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-filesystem-log-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\filesystem.log.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\filesystem.log.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
