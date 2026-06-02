# Отчёт: Task10 (Analysis of host journal~ dataset files)

## Описание задачи
Реализован отдельный этап анализа формата `TRAIN/journal~` на основе `temp_data/sort-path-host-file.json` с генерацией документации RU/EN.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_journal_tilde_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/journal~.md`
- `docs/en/analysis-dataset/host/journal~.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task10(Analysis of host journal~ dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task10(Analysis of host journal~ dataset files)_report.md`
- `temp_data/analysis-host-journal-tilde-summary.json`

## Описание структуры JSON
- бинарная сигнатура: `LPKSHHRH`
- тип: бинарный container
- статус пригодности: `NEEDS_CUSTOM_PARSER`

## Логика группировки путей
1. Считывается `sort-path-host-file.json`.
2. Выбирается bucket: `TRAIN -> journal~`.
3. Параллельно читается `sort-path-dns-file.json` для валидации контекста DNS/Host без смешивания данных.
4. Для анализа берётся ограниченный sample файлов и только безопасный header sample bytes.

## Пример итогового JSON
```json
{
  "scope": {
    "role": "TRAIN",
    "format": "journal~",
    "total_files_count": 1,
    "sampled_files_count": 1,
    "max_files_per_format": 30
  },
  "path_grouping": {
    "source_json_host": "sort-path-host-file.json",
    "source_json_dns": "sort-path-dns-file.json",
    "host_role_bucket": "TRAIN",
    "host_format_bucket": "journal~",
    "dns_formats_detected_count": 3
  },
  "final_status": "NEEDS_CUSTOM_PARSER"
}
```

## Результат
- Всего файлов формата: `1`.
- Sample-файлов проанализировано: `1`.
- Итоговый статус: `NEEDS_CUSTOM_PARSER`.

## Артефакты
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-journal-tilde-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\journal~.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\journal~.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
