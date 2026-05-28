# Отчёт: анализ Host-датасетов (этап 1)

## Краткое описание выполненной задачи
Реализован первый этап анализа Host-датасетов: поиск файлов в директории Host-датасетов, распределение по ролям (`TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`) и сохранение структуры в JSON.

## Какие файлы были добавлены или изменены
### Добавлены
- `scripts/handlers/host_dataset_handler.py`
- `report/ru/host_dataset_analysis_report.md`
- `report/en/host_dataset_analysis_report.md`

### Изменены
- `manage.py`
- `.env.example`

## Какие команды были добавлены в manage.py
Добавлена отдельная команда запуска анализа Host-датасетов:

```bash
python manage.py host dataset analyze
```

## Какие JSON-файлы создаются
- `host-path-file.json` — полные пути к найденным файлам Host-датасетов по ролям.
- `host-file.json` — имена файлов Host-датасетов по ролям.

Структура ролей в обоих JSON:
- `TRAIN`
- `TEST`
- `VALIDATION`
- `EXPERIMENTS`

## Где сохраняются результаты
Оба JSON-файла сохраняются в директорию из переменной окружения `PATH_TEMP_DATA`.

## Краткое описание логики работы скрипта
1. `manage.py` получает команду `host dataset analyze` и вызывает `HostDatasetHandler`.
2. Обработчик читает путь из `PATH_HOST_DATASETS` и рекурсивно сканирует файлы.
3. Роль определяется по токенам в пути (`train/test/validation/experiment`).
4. Формируются:
   - `host-path-file.json` — пути к файлам;
   - `host-file.json` — имена файлов.
5. Данные дедуплицируются, сортируются и сохраняются в `PATH_TEMP_DATA`.
