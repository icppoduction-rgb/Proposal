# Архитектура handlers: save_sort

## Оглавление

- [1. Назначение](#1-назначение)
- [2. Файлы пакета](#2-файлы-пакета)
- [3. Как запускается service](#3-как-запускается-service)
- [4. Цепочка вызовов](#4-цепочка-вызовов)
- [5. Router functions](#5-router-functions)
- [6. DNSSortedPathExportHandler](#6-dnssortedpathexporthandler)
- [7. HostSortedPathExportHandler](#7-hostsortedpathexporthandler)
- [8. Выходные JSON-артефакты](#8-выходные-json-артефакты)
- [9. Ошибки и ограничения](#9-ошибки-и-ограничения)

## 1. Назначение

`scripts/handlers/save_sort` сканирует уже отсортированную структуру датасетов и сохраняет JSON с путями файлов, сгруппированными по ролям и форматам.

Этот service не копирует и не перемещает файлы. Он только читает структуру `PATH_*_DATASETS_FILTER` и формирует индекс для content-analysis handlers.

## 2. Файлы пакета

| Файл | Назначение |
|---|---|
| `router_save.py` | Маршрутизирует `save-sort-host-dataset-handler` и `save-sort-dns-dataset-handler`. |
| `save_sort_dns_path_handler.py` | Экспортирует пути DNS-файлов. |
| `save_sort_host_path_handler.py` | Экспортирует пути Host-файлов. |
| `__init__.py` | Package marker. |

## 3. Как запускается service

DNS:

```bash
python manage.py handlers save-sort save-sort-dns-dataset-handler
```

Host:

```bash
python manage.py handlers save-sort save-sort-host-dataset-handler
```

Перед запуском должен быть выполнен `sort`, чтобы директории `PATH_DNS_DATASETS_FILTER` или `PATH_HOST_DATASETS_FILTER` уже существовали.

## 4. Цепочка вызовов

DNS:

```text
python manage.py handlers save-sort save-sort-dns-dataset-handler
-> router_commands(...)
-> router_commands_handlers("save-sort", "save-sort-dns-dataset-handler")
-> router_save("save-sort-dns-dataset-handler")
-> save_sort_dns_dataset_handler()
-> DNSSortedPathExportHandler(PATH_DNS_DATASETS_FILTER, PATH_TEMP_DATA)
-> export_paths()
-> _validate_source_root()
-> _scan_role_directory(...)
-> JsonDataManager(sort-path-dns-file.json).write(...)
```

Host:

```text
python manage.py handlers save-sort save-sort-host-dataset-handler
-> router_save("save-sort-host-dataset-handler")
-> save_sort_host_dataset_handler()
-> HostSortedPathExportHandler(PATH_HOST_DATASETS_FILTER, PATH_TEMP_DATA)
-> export_paths()
-> _scan_role_directory(...)
-> JsonDataManager(sort-path-host-file.json).write(...)
```

## 5. Router functions

### `router_save(action: str)`

| Action | Вызываемая функция |
|---|---|
| `save-sort-host-dataset-handler` | `save_sort_host_dataset_handler()` |
| `save-sort-dns-dataset-handler` | `save_sort_dns_dataset_handler()` |
| другое значение | печатает `manage_commands` |

## 6. DNSSortedPathExportHandler

Файл:

- `scripts/handlers/save_sort/save_sort_dns_path_handler.py`

### Классы

| Класс | Назначение |
|---|---|
| `DNSSortedPathExportResult` | Dataclass результата экспорта DNS путей. |
| `DNSSortedPathExportHandler` | Сканирует `PATH_DNS_DATASETS_FILTER`. |

### Роли

```text
TRAIN, TEST, VALIDATION, EXPERIMENTS
```

### Основной метод

`export_paths()`:

1. Проверяет source root через `_validate_source_root()`.
2. Создает структуру `{role: {}}`.
3. Для каждой роли ищет директорию `PATH_DNS_DATASETS_FILTER/<ROLE>`.
4. Сканирует format-директории через `_scan_role_directory()`.
5. Считает количество файлов.
6. Пишет `sort-path-dns-file.json`.
7. Пишет `sort-path-dns-file-summary.json`.
8. Возвращает `DNSSortedPathExportResult`.

## 7. HostSortedPathExportHandler

Файл:

- `scripts/handlers/save_sort/save_sort_host_path_handler.py`

### Классы

| Класс | Назначение |
|---|---|
| `HostSortedPathExportResult` | Dataclass результата экспорта Host путей. |
| `HostSortedPathExportHandler` | Сканирует `PATH_HOST_DATASETS_FILTER`. |

### Роли

```text
TRAIN, TEST, VALIDATION
```

### Основной метод

`export_paths()` повторяет DNS-логику, но работает с Host root и пишет Host JSON.

### `_scan_role_directory(role_directory)`

Общий алгоритм:

1. Итерируется по дочерним директориям роли.
2. Каждая дочерняя директория считается `format`.
3. Рекурсивно собирает все файлы через `format_directory.rglob("*")`.
4. Сохраняет абсолютные пути `path.resolve()`.
5. Возвращает `{format_name: [paths]}` только для непустых format-директорий.

## 8. Выходные JSON-артефакты

DNS:

```text
PATH_TEMP_DATA/sort-path-dns-file.json
PATH_TEMP_DATA/sort-path-dns-file-summary.json
```

Host:

```text
PATH_TEMP_DATA/sort-path-host-file.json
PATH_TEMP_DATA/sort-path-host-file-summary.json
```

Основной JSON имеет форму:

```json
{
  "TRAIN": {
    "csv": ["/absolute/path/file.csv"]
  },
  "TEST": {},
  "VALIDATION": {}
}
```

Summary содержит:

- `json_file`;
- `scanned_files_count`;
- `counts_by_role_and_format`.

## 9. Ошибки и ограничения

- Если root path не задан, выбрасывается `ValueError`.
- Если root path не существует, выбрасывается `FileNotFoundError`.
- Если root path не директория, выбрасывается `NotADirectoryError`.
- Пустые format-директории не попадают в итоговый JSON.
- Service не проверяет содержимое файлов; он индексирует только пути.
