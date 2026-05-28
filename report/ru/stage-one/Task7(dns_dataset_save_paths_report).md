# Отчёт: экспорт путей отсортированных DNS-датасетов в JSON (этап 7)

## Описание задачи
Реализован обработчик сохранения путей отсортированных DNS-датасетов в JSON.
Источник: `PATH_DNS_DATASETS_FILTER`.
Целевой файл: `PATH_TEMP_DATA/sort-path-dns-file.json`.

## Какие файлы были добавлены
- `scripts/handlers/save_sort_dns_path_handler.py`
- `report/ru/dns_dataset_save_paths_report.md`
- `report/en/dns_dataset_save_paths_report.md`

## Какие файлы были изменены
- `manage.py`

## Команда запуска
- `python manage.py dns dataset save-paths`

Дополнительно поддерживается alias:
- `python manage.py dataset dns save-paths`

`manage.py` остаётся только точкой входа, основная логика реализована в `scripts/handlers/save_sort_dns_path_handler.py`.

## Описание структуры JSON
Итоговый JSON имеет структуру:

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
  "EXPERIMENTS": {
    "format": ["absolute_path_to_file"]
  }
}
```

- Уровень 1: роль датасета (`TRAIN`, `TEST`, `VALIDATION`, `EXPERIMENTS`).
- Уровень 2: формат файла (имя format-директории).
- Значение: список абсолютных путей файлов.

## Логика группировки путей
1. Сканируется `PATH_DNS_DATASETS_FILTER` по ролям.
2. Внутри роли сканируются папки форматов.
3. Для каждого формата собираются все файлы (`rglob('*')`).
4. Пути нормализуются в абсолютные через `Path.resolve()`.
5. Формируется структура `ROLE -> FORMAT -> [PATHS]`.
6. JSON сохраняется в `PATH_TEMP_DATA/sort-path-dns-file.json`.

Дополнительно сохраняется summary:
- `PATH_TEMP_DATA/sort-path-dns-file-summary.json`.

## Пример итогового JSON (фрагмент)
```json
{
  "TRAIN": {
    "csv": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\dns\\TRAIN\\csv\\benign_domains.csv"
    ],
    "pcap": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\dns\\TRAIN\\pcap\\benign.pcap"
    ]
  },
  "TEST": {
    "csv": [
      "C:\\Users\\fmark\\PythonProjects\\storages\\datasets-filter\\dns\\TEST\\csv\\dataset.csv"
    ]
  }
}
```

## Результат запуска
- Создан файл: `PATH_TEMP_DATA/sort-path-dns-file.json`
- `scanned_files_count`: `35`
- Группировка по ролям и форматам подтверждена.
- Исходные DNS-данные не изменяются и не удаляются.
