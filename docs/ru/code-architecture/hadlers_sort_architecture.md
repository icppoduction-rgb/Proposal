# Архитектура handlers: sort

## Оглавление

- [1. Назначение](#1-назначение)
- [2. Файлы пакета](#2-файлы-пакета)
- [3. Как запускается service](#3-как-запускается-service)
- [4. Цепочка вызовов](#4-цепочка-вызовов)
- [5. Router functions](#5-router-functions)
- [6. DNSDatasetSortHandler](#6-dnsdatasetsorthandler)
- [7. HostDatasetSortHandler](#7-hostdatasetsorthandler)
- [8. Логика materialize файла](#8-логика-materialize-файла)
- [9. Выходные артефакты](#9-выходные-артефакты)
- [10. Ошибки и ограничения](#10-ошибки-и-ограничения)

## 1. Назначение

`scripts/handlers/sort` сортирует найденные файлы по ролям и форматам. Service создает физическую директорию вида:

```text
PATH_*_DATASETS_FILTER/
└── <ROLE>/
    └── <format>/
        └── <file>
```

DNS сортируется на основе `dns-path-file.json` и `dns-file.json`. Host сортируется на основе отфильтрованных файлов `filter_dataset-host-path-file.json` и `filter_dataset-host-file.json`.

## 2. Файлы пакета

| Файл | Назначение |
|---|---|
| `router_sort.py` | Маршрутизирует `sort-host-dataset-handler` и `sort-dns-dataset-handler`. |
| `sort_dns_dataset_handler.py` | Сортирует DNS-файлы по ролям и format group. |
| `sort_host_dataset_handler.py` | Сортирует Host-файлы по ролям и format group. |
| `__init__.py` | Package marker. |

## 3. Как запускается service

DNS:

```bash
python manage.py handlers sort sort-dns-dataset-handler
```

Host:

```bash
python manage.py handlers sort sort-host-dataset-handler
```

Перед запуском DNS route должны существовать:

```text
PATH_TEMP_DATA/dns-path-file.json
PATH_TEMP_DATA/dns-file.json
```

Перед запуском Host route должны существовать:

```text
PATH_TEMP_DATA/filter_dataset-host-path-file.json
PATH_TEMP_DATA/filter_dataset-host-file.json
```

## 4. Цепочка вызовов

DNS:

```text
python manage.py handlers sort sort-dns-dataset-handler
-> manage.manage()
-> router_commands(...)
-> router_commands_handlers("sort", "sort-dns-dataset-handler")
-> router_sort("sort-dns-dataset-handler")
-> sort_dns_dataset_handler()
-> DNSDatasetSortHandler(PATH_TEMP_DATA, PATH_DNS_DATASETS_FILTER)
-> sort_and_prepare()
-> _validate_output_root()
-> JsonDataManager(...).read(...)
-> _detect_format_group(...)
-> _build_destination_path(...)
-> _materialize_file(...)
-> JsonDataManager(sort-dns-format-summary.json).write(...)
```

Host:

```text
python manage.py handlers sort sort-host-dataset-handler
-> router_sort("sort-host-dataset-handler")
-> sort_host_dataset_handler()
-> HostDatasetSortHandler(PATH_TEMP_DATA, PATH_HOST_DATASETS_FILTER)
-> sort_and_prepare()
-> _detect_format_group(...)
-> _materialize_file(...)
-> JsonDataManager(sort-host-format-summary.json).write(...)
```

## 5. Router functions

### `router_sort(action: str)`

| Action | Вызываемая функция |
|---|---|
| `sort-host-dataset-handler` | `sort_host_dataset_handler()` |
| `sort-dns-dataset-handler` | `sort_dns_dataset_handler()` |
| другое значение | печатает `manage_commands` |

### `sort_host_dataset_handler()`

Создает `HostDatasetSortHandler` с:

- `temp_data_path=PATH_TEMP_DATA`;
- `host_datasets_filter_path=PATH_HOST_DATASETS_FILTER`.

### `sort_dns_dataset_handler()`

Создает `DNSDatasetSortHandler` с:

- `temp_data_path=PATH_TEMP_DATA`;
- `dns_datasets_filter_path=PATH_DNS_DATASETS_FILTER`.

## 6. DNSDatasetSortHandler

Файл:

- `scripts/handlers/sort/sort_dns_dataset_handler.py`

### Классы

| Класс | Назначение |
|---|---|
| `DNSDatasetSortResult` | Dataclass результата сортировки DNS. |
| `DNSDatasetSortHandler` | Основной DNS sort handler. |

### Роли

```text
TRAIN, TEST, VALIDATION, EXPERIMENTS
```

### Основной метод

`sort_and_prepare()`:

1. Проверяет целевую директорию через `_validate_output_root()`.
2. Читает `dns-path-file.json`.
3. Читает `dns-file.json`.
4. Проверяет обязательные роли через `_validate_source_json()`.
5. Нормализует имена файлов через `_normalize_file_names()`.
6. Нормализует пути через `_normalize_file_paths()`.
7. Создает базовые role-директории через `_create_base_role_directories()`.
8. Для каждого файла определяет формат через `_detect_format_group()`.
9. Создает директорию `<ROLE>/<format>`.
10. Определяет destination через `_build_destination_path()`.
11. Создает hardlink или копию через `_materialize_file()`.
12. Пишет `sort-dns-format-summary.json`.
13. Возвращает `DNSDatasetSortResult`.

### DNS format detection

`_detect_format_group(file_name)`:

| Условие | Format group |
|---|---|
| имя заканчивается на `.pcap.csv` | `pcap.csv` |
| имя заканчивается на `.pcap` | `pcap` |
| имя заканчивается на `.csv` | `csv` |
| имя заканчивается на `.txt` | `txt` |
| есть другое расширение | suffix без точки |
| расширения нет | имя файла |

## 7. HostDatasetSortHandler

Файл:

- `scripts/handlers/sort/sort_host_dataset_handler.py`

### Классы

| Класс | Назначение |
|---|---|
| `HostDatasetSortResult` | Dataclass результата сортировки Host. |
| `HostDatasetSortHandler` | Основной Host sort handler. |

### Роли

```text
TRAIN, TEST, VALIDATION
```

### Основной метод

`sort_and_prepare()` повторяет общую сортировочную логику DNS, но читает:

- `filter_dataset-host-path-file.json`;
- `filter_dataset-host-file.json`.

### Host format detection

`_detect_format_group(file_name)` содержит специальные правила для Host-имен:

| Условие | Format group |
|---|---|
| `netflow_day-\d+` | `netflow_day` |
| `wls_day-\d+` | `wls_day` |
| имя заканчивается на `journal~` | `journal~` |
| `messages` | `messages` |
| `messages.<n>` | `messages-<n>` |
| `mainlog.<n>` | `mainlog-<n>` |
| `log.<n>` | `log-<n>` |
| `*.pcap.<timestamp>` | `pcap` |
| `info.<n>` | `info-<n>` |
| semantic logs: `auth.log`, `cpu.log`, `diskio.log`, ... | соответствующий semantic format |
| rotated `.log`, `.json`, `syslog` | `log-<n>`, `json-<n>`, `syslog-<n>` |
| `.netflow_ids` | `netflow_ids` |
| другое расширение | suffix без точки |
| расширения нет | имя файла |

## 8. Логика materialize файла

Оба sort handlers используют одинаковый алгоритм:

```text
source_path
-> _build_destination_path(role_dir, source_path)
-> if destination exists and samefile: skip
-> else _materialize_file(source_path, destination_path)
```

`_materialize_file()`:

1. Если destination уже существует и указывает на source, возвращает `True`.
2. Если destination существует, но это другой файл, выбрасывает `FileExistsError`.
3. Пытается создать hardlink через `os.link(source_path, destination_path)`.
4. Если `os.link` падает с `OSError`, делает `shutil.copy2(...)`.
5. Возвращает `True` для hardlink, `False` для копии.

Коллизии имен решаются через `_destination_name_with_hash()`, где hash строится из полного исходного пути.

## 9. Выходные артефакты

DNS:

```text
PATH_DNS_DATASETS_FILTER/<ROLE>/<format>/*
PATH_TEMP_DATA/sort-dns-format-summary.json
```

Host:

```text
PATH_HOST_DATASETS_FILTER/<ROLE>/<format>/*
PATH_TEMP_DATA/sort-host-format-summary.json
```

Summary содержит:

- `sorted_root_path`;
- `created_links_count`;
- `copied_files_count`;
- `skipped_existing_count`;
- `missing_source_count`;
- `name_mismatch_count`;
- `files_by_role_and_format`.

## 10. Ошибки и ограничения

- Sort stage зависит от свежести входных JSON.
- Host sort ожидает результат `filter_dataset`, а не исходный `host-path-file.json`.
- Если обязательные роли отсутствуют в JSON, handler выбрасывает `ValueError`.
- Если исходный файл отсутствует, увеличивается `missing_source_count`, файл пропускается.
- Hardlink может не работать между разными файловыми системами; предусмотрен fallback на copy.
- При новых форматах Host может потребоваться обновить `_detect_format_group()`.
