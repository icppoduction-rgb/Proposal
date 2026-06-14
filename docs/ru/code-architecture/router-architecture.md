# Архитектура CLI и маршрутизации команд

## Entry point: `manage.py`

`manage.py` создает `argparse.ArgumentParser` и принимает три позиционных аргумента:

| Аргумент | Назначение |
|---|---|
| `module` | Верхний уровень: `handlers` или `stage-two`. |
| `service` | Сервис внутри модуля, например `analyze-dataset`, `normalize-dns`. |
| `action` | Опциональное действие. Для Stage Two используется как `limit` или trace artifact ID/path. |

Код вызывает `parse_known_args()`, поэтому неизвестные дополнительные аргументы не приводят к ошибке argparse и фактически игнорируются. После парсинга вызывается `scripts.router_script.router_commands(args.module, args.service, args.action)`.

## Верхнеуровневый router

`router_commands()` в `scripts/router_script.py` поддерживает два module:

| module | Router | Назначение |
|---|---|---|
| `handlers` | `scripts.handlers.router_handler.router_commands_handlers` | Stage One файловая подготовка и анализ содержимого. |
| `stage-two` | `scripts.stage_two.cli.router_stage_two` | Stage Two catalog/normalization/quality/traceability. |
| другое/пусто | печать `manage_commands` | Нет исключения и нет non-zero exit code. |

## Handlers router

`router_commands_handlers(service, action)` маршрутизирует service:

| service | Router | Назначение |
|---|---|---|
| `analyze-dataset` | `router_analyze(action)` | Первичный обход DNS/host исходных директорий. |
| `filter-dataset` | `router_filter(action)` | Фильтрация host-файлов по whitelist правилам. |
| `sort` | `router_sort(action)` | Копирование файлов в отсортированное дерево по роли/формату. |
| `save-sort` | `router_save(action)` | Экспорт списка путей из отсортированного дерева. |
| `dns-analyze` | `router_dns(action)` | Анализ содержимого DNS buckets. |
| `host-analyze` | `router_host(action)` | Анализ содержимого host buckets. |

## Stage Two router

`router_stage_two(service, action)` поддерживает команды:

| Команда | `action` | Назначение |
|---|---|---|
| `bootstrap-storage` | не используется | Создает структуру Stage Two storage. |
| `catalog-ingest` | не используется | Сканирует configured roots и регистрирует raw-файлы в PostgreSQL Catalog. |
| `seed-parser-registry` | не используется | Регистрирует `schema_versions` и parser registry. |
| `normalize-dns` | optional integer limit | Нормализует DNS-файлы со статусом `READY_FOR_PARSING`. |
| `normalize-host` | optional integer limit | Нормализует host-файлы со статусом `READY_FOR_PARSING`. |
| `run-duckdb-checks` | не используется | Запускает аналитические DuckDB checks и регистрирует report. |
| `run-leakage-checks` | не используется | Запускает leakage checks и регистрирует report. |
| `trace-artifact` | model-ready ID или path | Печатает traceability chain. |

`normalize-*` валидирует `action`: если он указан, он должен быть неотрицательным integer. Ошибка `ValueError` перехватывается и печатается как JSON-like dict.

## Примеры команд

```powershell
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers dns-analyze analyze-train-csv-content
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two normalize-dns 100
python manage.py stage-two trace-artifact 1
```

## Важные ограничения маршрутизации

| Ограничение | Последствие |
|---|---|
| `manage.py` принимает только `module service action`. | Нельзя передать несколько именованных параметров без изменения CLI. |
| `parse_known_args()` игнорирует extra args. | Опечатки в дополнительных аргументах не считаются ошибкой. |
| Unknown module/service/action печатает help. | Shell exit code может оставаться успешным, что важно для CI. |
| Routing реализован через `if/elif` и dict routes. | Новые команды требуют явной регистрации в router-файлах. |
