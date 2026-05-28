# Отчёт: экспорт путей отсортированных Host-датасетов в JSON (этап 5)

## Описание задачи
Реализован обработчик сохранения путей отсортированных Host-датасетов в JSON.
Источник данных: `PATH_HOST_DATASETS_FILTER`.
Целевой файл: `PATH_TEMP_DATA/sort-path-host-file.json`.

## Какие файлы были добавлены
- `scripts/handlers/save_sort_host_path_handler.py`
- `report/ru/host_dataset_save_paths_report.md`
- `report/en/host_dataset_save_paths_report.md`

## Какие файлы были изменены
- `manage.py`

## Команда запуска
- `python manage.py host dataset save-paths`

`manage.py` используется только как entrypoint. Основная логика находится в `scripts/handlers/save_sort_host_path_handler.py`.

## Описание структуры JSON
Итоговый JSON:

```json
{
  "TRAIN": {
    "format": ["absolute_path_to_file"]
  },
  "TEST": {
    "format": ["absolute_path_to_file"]
  },
  "VALIDATION": {
    "format": ["absolute_path_to_file"]
  },
    "format": ["absolute_path_to_file"]
  }
}
```

- Первый уровень — роль датасета (`TRAIN`, `TEST`, `VALIDATION`).
- Второй уровень — формат файла (имя format-папки в отсортированной структуре).
- Значение — список абсолютных путей к файлам.

## Логика группировки путей
1. Сканируется `PATH_HOST_DATASETS_FILTER` по ролям.
2. Внутри каждой роли сканируются директории форматов.
3. Для каждого формата собираются все файлы (`rglob('*')`), пути нормализуются в абсолютные через `Path.resolve()`.
4. Формируется структура `ROLE -> FORMAT -> [PATHS]`.
5. JSON сохраняется в `PATH_TEMP_DATA/sort-path-host-file.json`.

Дополнительно сохраняется сводка в `PATH_TEMP_DATA/sort-path-host-file-summary.json`.

## Пример итогового JSON (фрагмент)
```json
{
  "TRAIN": {
    "auth.log": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\host\\TRAIN\\auth.log\\2022-01-13-system.auth.log"
    ],
    "cpu.log": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\host\\TRAIN\\cpu.log\\2022-01-13-system.cpu.log"
    ]
  },
  "TEST": {
    "bson": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\host\\TEST\\bson\\1000.bson"
    ]
  }
}
```

## Результат запуска
- Создан файл: `PATH_TEMP_DATA/sort-path-host-file.json`
- Проверено группирование по ролям и форматам.
- Исходные данные не изменяются и не удаляются.
