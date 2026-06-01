# Отчёт: Task7 (Analysis of host ghc dataset files)

## Описание задачи
Реализован отдельный этап анализа формата `TRAIN/ghc` на основе `temp_data/sort-path-host-file.json` с генерацией документации RU/EN.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_ghc_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/ghc.md`
- `docs/en/analysis-dataset/host/ghc.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task7(Analysis of host ghc dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task7(Analysis of host ghc dataset files)_report.md`
- `temp_data/analysis-host-ghc-summary.json`

## Описание структуры JSON
- формат trace: `<module>+0x<offset>`
- тип: текстовые последовательности
- статус пригодности: `NEEDS_CUSTOM_PARSER`

## Логика группировки путей
1. Считывается `sort-path-host-file.json`.
2. Выбирается bucket: `TRAIN -> ghc`.
3. Параллельно читается `sort-path-dns-file.json` для валидации контекста DNS/Host без смешивания данных.
4. Для анализа берётся ограниченный sample файлов и строк.

## Пример итогового JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "ghc",
    "total_files_count": 56158,
    "sampled_files_count": 30,
    "max_files_per_format": 30,
    "max_lines_per_file": 1000
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "ghc",
    "dns_formats_detected_count": 3
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

## Результат
- Всего файлов формата: `56158`.
- Sample-файлов проанализировано: `30`.
- Итоговый статус: `NEEDS_CUSTOM_PARSER`.

## Артефакты
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-ghc-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\ghc.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\ghc.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
