# Архитектура handlers: analyze_dataset

## Оглавление

- [1. Назначение](#1-назначение)
- [2. Файлы пакета](#2-файлы-пакета)
- [3. Как запускается service](#3-как-запускается-service)
- [4. Цепочка вызовов](#4-цепочка-вызовов)
- [5. Router functions](#5-router-functions)
- [6. DNSDatasetHandler](#6-dnsdatasethandler)
- [7. HostDatasetHandler](#7-hostdatasethandler)
- [8. Выходные JSON-артефакты](#8-выходные-json-артефакты)
- [9. Ошибки и ограничения](#9-ошибки-и-ограничения)

## 1. Назначение

`scripts/handlers/analyze_dataset` выполняет первый этап пайплайна: рекурсивно сканирует исходные DNS/Host директории, определяет роль файлов и сохраняет промежуточные JSON-файлы со списками путей и имен.

Этот service не анализирует содержимое файлов. Его задача - построить индекс исходных файлов для следующих этапов: `filter_dataset`, `sort`, `save_sort`, `dns_analyze`, `host_analyze`.

## 2. Файлы пакета

| Файл | Назначение |
|---|---|
| `router_analyze.py` | Маршрутизирует action внутри service `analyze-dataset`. |
| `dns_dataset_handler.py` | Сканирует DNS датасеты и пишет `dns-path-file.json`, `dns-file.json`. |
| `host_dataset_handler.py` | Сканирует Host датасеты и пишет `host-path-file.json`, `host-file.json`. |
| `__init__.py` | Package marker, публичные классы не экспортирует. |

## 3. Как запускается service

Команды:

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers analyze-dataset host-dataset-handler
```

`manage.py` принимает аргументы:

```text
module=handlers
service=analyze-dataset
action=dns-dataset-handler | host-dataset-handler
```

Затем команда проходит через:

```text
manage.manage()
-> router_commands()
-> router_commands_handlers()
-> router_analyze()
```

## 4. Цепочка вызовов

DNS:

```text
python manage.py handlers analyze-dataset dns-dataset-handler
-> manage.manage()
-> scripts.router_script.router_commands("handlers", "analyze-dataset", "dns-dataset-handler")
-> scripts.handlers.router_handler.router_commands_handlers("analyze-dataset", "dns-dataset-handler")
-> scripts.handlers.analyze_dataset.router_analyze.router_analyze("dns-dataset-handler")
-> dns_dataset_handler()
-> DNSDatasetHandler(PATH_DNS_DATASETS, PATH_TEMP_DATA)
-> DNSDatasetHandler.analyze_and_save()
-> JsonDataManager(...).write(...)
```

Host:

```text
python manage.py handlers analyze-dataset host-dataset-handler
-> manage.manage()
-> router_commands(...)
-> router_commands_handlers(...)
-> router_analyze("host-dataset-handler")
-> host_dataset_handler()
-> HostDatasetHandler(PATH_HOST_DATASETS, PATH_TEMP_DATA)
-> HostDatasetHandler.analyze_and_save()
-> JsonDataManager(...).write(...)
```

## 5. Router functions

### `router_analyze(action: str)`

Выбирает обработчик по `action`.

| Action | Вызываемая функция |
|---|---|
| `dns-dataset-handler` | `dns_dataset_handler()` |
| `host-dataset-handler` | `host_dataset_handler()` |
| другое значение | печатает `manage_commands` |

### `dns_dataset_handler()`

Создает `DNSDatasetHandler` с путями из `config.py`:

- `PATH_DNS_DATASETS`;
- `PATH_TEMP_DATA`.

После выполнения печатает:

- путь к JSON с полными путями;
- путь к JSON с именами файлов.

### `host_dataset_handler()`

Создает `HostDatasetHandler` с путями из `config.py`:

- `PATH_HOST_DATASETS`;
- `PATH_TEMP_DATA`.

После выполнения печатает аналогичный результат для Host.

## 6. DNSDatasetHandler

Файл:

- `scripts/handlers/analyze_dataset/dns_dataset_handler.py`

### Классы

| Класс | Назначение |
|---|---|
| `DNSAnalysisResult` | Immutable dataclass результата: пути JSON и сгруппированные данные. |
| `DNSDatasetHandler` | Основной обработчик сканирования DNS датасетов. |

### Роли

`DNSDatasetHandler.ROLE_KEYWORDS`:

| Роль | Токены в пути |
|---|---|
| `TRAIN` | `train`, `training` |
| `TEST` | `test`, `testing` |
| `VALIDATION` | `validation`, `valid`, `val`, `dev`, `eval` |
| `EXPERIMENTS` | `experiment`, `experiments`, `exp`, `sandbox`, `trial` |

Если роль не найдена, используется `EXPERIMENTS`.

### Основной метод

`analyze_and_save()`:

1. Вызывает `_validate_dns_root_path()`.
2. Создает пустые `set`-структуры ролей через `_init_role_sets()`.
3. Получает директории с файлами через `_walk_dns_files()`.
4. Для каждой директории определяет роль через `_detect_role(path)`.
5. Добавляет полный путь файла в `paths_by_role_set`.
6. Добавляет имя файла в `files_by_role_set`.
7. Преобразует множества в отсортированные списки через `_prepare_output()`.
8. Пишет `dns-path-file.json`.
9. Пишет `dns-file.json`.
10. Возвращает `DNSAnalysisResult`.

### Вспомогательные методы

| Метод | Логика |
|---|---|
| `_validate_dns_root_path()` | Проверяет, что `PATH_DNS_DATASETS` задан, существует и является директорией. |
| `_walk_dns_files()` | Рекурсивно проходит по `dns_datasets_path.rglob("*")` и группирует файлы по директории. |
| `_detect_role(path)` | Разбивает путь на токены и ищет role keyword. |
| `_tokenize(value)` | Делит строку регулярным выражением `[^a-z0-9]+`. |
| `_init_role_sets()` | Создает `{role: set()}` для всех DNS ролей. |
| `_prepare_output(role_map)` | Возвращает `{role: sorted(list)}`. |

## 7. HostDatasetHandler

Файл:

- `scripts/handlers/analyze_dataset/host_dataset_handler.py`

### Классы

| Класс | Назначение |
|---|---|
| `HostAnalysisResult` | Immutable dataclass результата: пути JSON и сгруппированные данные. |
| `HostDatasetHandler` | Основной обработчик сканирования Host датасетов. |

### Роли

`HostDatasetHandler.ROLE_KEYWORDS`:

| Роль | Токены в пути |
|---|---|
| `TRAIN` | `train`, `training` |
| `TEST` | `test`, `testing` |
| `VALIDATION` | `validation`, `valid`, `val`, `dev`, `eval` |

Если роль не найдена, используется `TEST`.

### Основной метод

`analyze_and_save()` работает так же, как DNS-версия, но пишет Host-артефакты:

- `host-path-file.json`;
- `host-file.json`.

### Вспомогательные методы

| Метод | Логика |
|---|---|
| `_validate_host_root_path()` | Проверяет, что `PATH_HOST_DATASETS` задан, существует и является директорией. |
| `_walk_host_files()` | Рекурсивно группирует найденные файлы по директории. |
| `_detect_role(path)` | Определяет роль по токенам пути. |
| `_tokenize(value)` | Нормализует строку пути в набор токенов. |
| `_init_role_sets()` | Создает `{role: set()}` для Host ролей. |
| `_prepare_output(role_map)` | Преобразует множества в отсортированные списки для JSON. |

## 8. Выходные JSON-артефакты

DNS:

```text
PATH_TEMP_DATA/dns-path-file.json
PATH_TEMP_DATA/dns-file.json
```

Host:

```text
PATH_TEMP_DATA/host-path-file.json
PATH_TEMP_DATA/host-file.json
```

Форма данных:

```json
{
  "TRAIN": ["/absolute/path/to/file"],
  "TEST": [],
  "VALIDATION": []
}
```

Для `*-file.json` вместо полных путей сохраняются только basename файлов.

## 9. Ошибки и ограничения

- Обработчики не проверяют содержимое файлов, только путь и имя.
- Роль определяется по токенам пути, поэтому качество классификации зависит от структуры директорий.
- DNS поддерживает роль `EXPERIMENTS`, Host - нет.
- Нераспознанные Host файлы попадают в `TEST`, что может быть неожиданно для новых датасетов.
- Следующие этапы зависят от актуальности JSON-файлов в `PATH_TEMP_DATA`.
