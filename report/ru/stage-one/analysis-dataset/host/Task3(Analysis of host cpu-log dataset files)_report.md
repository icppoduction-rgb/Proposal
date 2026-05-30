# Отчёт: Task3 (Analysis of host cpu-log dataset files)

## Описание задачи
Реализован этап анализа формата `TRAIN/cpu.log` на основе `temp_data/sort-path-host-file.json` с генерацией RU/EN документации.

## Какие файлы были добавлены/изменены
- `scripts/handlers/analyze_host_cpu_log_dataset_handler.py`
- `manage.py`
- `docs/ru/analysis-dataset/host/cpu.log.md`
- `docs/en/analysis-dataset/host/cpu.log.md`
- `docs/ru/analysis-dataset/host/README.md`
- `docs/en/analysis-dataset/host/README.md`
- `report/ru/stage-one/analysis-dataset/host/Task3(Analysis of host cpu-log dataset files)_report.md`
- `report/en/stage-one/analysis-dataset/host/Task3(Analysis of host cpu-log dataset files)_report.md`
- `temp_data/analysis-host-cpu-log-summary.json`

## Логика
1. Загружены пути `TRAIN/cpu.log`.
2. Выполнен анализ JSON-lines структуры и вложенных CPU полей.
3. Проверены timestamp, label-индикаторы и качество данных.
4. Зафиксированы смешанные схемы (metric rows + annotation rows).
5. Сгенерированы markdown-документы и обновлён host README.

## Результат
- Всего файлов формата: `13`.
- Sample-файлов проанализировано: `13`.
- Итоговый статус: `PARTIALLY_SUPPORTED`.

## Артефакты
- Summary JSON: `C:\Users\fmark\PythonProjects\Proposal\temp_data\analysis-host-cpu-log-summary.json`
- RU doc: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\cpu.log.md`
- EN doc: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\cpu.log.md`
- RU README: `C:\Users\fmark\PythonProjects\Proposal\docs\ru\analysis-dataset\host\README.md`
- EN README: `C:\Users\fmark\PythonProjects\Proposal\docs\en\analysis-dataset\host\README.md`
