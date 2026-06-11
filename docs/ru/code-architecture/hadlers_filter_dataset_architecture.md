# Архитектура handlers: filter_dataset

## Оглавление

- [1. Назначение](#1-назначение)
- [2. Файлы пакета](#2-файлы-пакета)
- [3. Как запускается service](#3-как-запускается-service)
- [4. Цепочка вызовов](#4-цепочка-вызовов)
- [5. Router functions](#5-router-functions)
- [6. HostDatasetFilterHandler](#6-hostdatasetfilterhandler)
- [7. Правила фильтрации](#7-правила-фильтрации)
- [8. Выходные артефакты](#8-выходные-артефакты)
- [9. Ошибки и ограничения](#9-ошибки-и-ограничения)

## 1. Назначение

`scripts/handlers/filter_dataset` фильтрует Host-датасеты после первичного сканирования. Service оставляет только те файлы, которые соответствуют роли, имени датасета и разрешенным расширениям.

DNS-файлы через этот service не проходят.

## 2. Файлы пакета

| Файл | Назначение |
|---|---|
| `router_filter.py` | Маршрутизирует action `filter-host-dataset-handler`. |
| `filter_host_dataset_handler.py` | Содержит `HostDatasetFilterHandler` и `HostFilterResult`. |
| `__init__.py` | Package marker. |

## 3. Как запускается service

```bash
python manage.py handlers filter-dataset filter-host-dataset-handler
```

Перед запуском должны существовать:

```text
PATH_TEMP_DATA/host-path-file.json
PATH_TEMP_DATA/host-file.json
```

Эти файлы создает:

```bash
python manage.py handlers analyze-dataset host-dataset-handler
```

## 4. Цепочка вызовов

```text
python manage.py handlers filter-dataset filter-host-dataset-handler
-> manage.manage()
-> router_commands("handlers", "filter-dataset", "filter-host-dataset-handler")
-> router_commands_handlers("filter-dataset", "filter-host-dataset-handler")
-> router_filter("filter-host-dataset-handler")
-> filter_host_dataset_handler()
-> HostDatasetFilterHandler(PATH_TEMP_DATA, PATH_FILTER_LOG)
-> HostDatasetFilterHandler.filter_and_save()
-> JsonDataManager(...).read(...)
-> HostDatasetFilterHandler._is_allowed_file(...)
-> JsonDataManager(...).write(...)
```

## 5. Router functions

### `router_filter(action: str)`

| Action | Вызываемая функция |
|---|---|
| `filter-host-dataset-handler` | `filter_host_dataset_handler()` |
| другое значение | печатает `manage_commands` |

### `filter_host_dataset_handler()`

Создает `HostDatasetFilterHandler` с:

- `temp_data_path=PATH_TEMP_DATA`;
- `log_file_path=PATH_FILTER_LOG`.

После выполнения печатает:

- пути итоговых JSON;
- путь лога;
- количество сохраненных и исключенных файлов;
- причины исключения.

## 6. HostDatasetFilterHandler

Файл:

- `scripts/handlers/filter_dataset/filter_host_dataset_handler.py`

### Классы

| Класс | Назначение |
|---|---|
| `HostFilterResult` | Dataclass результата фильтрации. |
| `HostDatasetFilterHandler` | Основной обработчик фильтрации Host-файлов. |

### Основной метод

`filter_and_save()`:

1. Читает `host-path-file.json`.
2. Читает `host-file.json`.
3. Проверяет наличие обязательных ролей через `_validate_source_json()`.
4. Нормализует имена файлов по ролям через `_normalize_files_by_role()`.
5. Для каждого пути проверяет тип значения.
6. Извлекает имя датасета через `_extract_dataset_name()`.
7. Проверяет, разрешен ли dataset для роли.
8. Проверяет файл через `_is_allowed_file()`.
9. Проверяет, что basename есть в `host-file.json`.
10. Сохраняет валидные пути и имена в set-структуры.
11. Пишет `filter_dataset-host-path-file.json`.
12. Пишет `filter_dataset-host-file.json`.
13. Возвращает `HostFilterResult`.

### Вспомогательные методы

| Метод | Логика |
|---|---|
| `_build_logger()` | Создает logger и file handler для лога исключений. |
| `_track_exclusion(...)` | Увеличивает счетчик причины и пишет строку в лог. |
| `_validate_source_json(...)` | Проверяет наличие `TRAIN`, `TEST`, `VALIDATION`. |
| `_normalize_files_by_role(...)` | Преобразует имена файлов в `set` по ролям. |
| `_is_allowed_file(...)` | Применяет правила разрешенных датасетов и расширений. |
| `_extract_dataset_name(file_path)` | Извлекает имя датасета из пути после сегмента `host`. |
| `_normalize_path_text(file_path)` | Приводит разделители пути к `/`. |
| `_path_name(file_path)` | Возвращает basename для POSIX/Windows путей. |
| `_init_role_sets()` | Создает пустые set-структуры ролей. |
| `_prepare_output(...)` | Преобразует множества в отсортированные списки. |

## 7. Правила фильтрации

### Роли и датасеты

| Роль | Разрешенные датасеты |
|---|---|
| `TRAIN` | `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset` |
| `TEST` | `Unified-Host-Network-Dataset -LANL`, `ISOT-Cloud-IDS-Dataset`, `Dynamic-Malware-Analysis-Dataset` |
| `VALIDATION` | `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets` |

### Расширения

| Датасет | Разрешенные расширения / правила |
|---|---|
| `ADFA IDS` | `.txt`, `.ghc`, `.csv`, `.netflow_ids`, `.xml` |
| `LID-DS 2021` | `.sc`, `.json` |
| `LID-DS 2019` | `.txt`, `.csv` |
| `Windows-Event-Log -OTRF-Security-Datasets` | `.json`, `.cap`, `.pcap`, `.pcapng` |
| `ISOT-Cloud-IDS-Dataset` | `.csv` |
| `Dynamic-Malware-Analysis-Dataset` | `.txt`, `.json`, `.bson`, `.log` |
| `Maintainable Log Dataset` | Только пути с `/logs/`, `/alerts_csv/`, `/labels/`, кроме бинарных/офисных расширений. |
| `LANL Dataset` | Все файлы разрешены. |
| `Unified-Host-Network-Dataset -LANL` | Все файлы разрешены. |

## 8. Выходные артефакты

```text
PATH_TEMP_DATA/filter_dataset-host-path-file.json
PATH_TEMP_DATA/filter_dataset-host-file.json
PATH_FILTER_LOG
```

`HostFilterResult` дополнительно возвращает:

- `kept_files_count`;
- `excluded_files_count`;
- `excluded_by_reason`;
- сгруппированные пути и имена файлов.

## 9. Ошибки и ограничения

- Фильтр зависит от структуры пути: имя датасета извлекается после сегмента `host`.
- Если путь не содержит ожидаемую структуру, файл исключается с причиной `dataset_name_not_detected`.
- Logger очищает старые handlers, чтобы не дублировать строки, и пишет лог в режиме `w`.
- `PATH_FILTER_LOG` должен быть строкой или совместимым path-like значением.
- Новые датасеты нужно явно добавить в `DATASET_ROLE_MAP` и `_is_allowed_file()`.
