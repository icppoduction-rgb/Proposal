# Архитектура кода

Этот раздел описывает фактическую реализацию `manage.py`, `scripts/*`, PostgreSQL Catalog и Stage Two на основе текущего кода проекта.

## Документы

| Документ | Назначение |
|---|---|
| [general-architecture.md](general-architecture.md) | Общая архитектура, основные слои и сквозной pipeline. |
| [router-architecture.md](router-architecture.md) | Точка входа `manage.py`, маршрутизация команд и поддерживаемые CLI-команды. |
| [hadlers_analyze_dataset_architecture.md](hadlers_analyze_dataset_architecture.md) | Первичный обход DNS/host датасетов и JSON-контракты discovery. |
| [hadlers_filter_dataset_architecture.md](hadlers_filter_dataset_architecture.md) | Host-фильтрация перед сортировкой. |
| [hadlers_sort_architecture.md](hadlers_sort_architecture.md) | Сортировка файлов по роли и формату. |
| [hadlers_save_sort_architecture.md](hadlers_save_sort_architecture.md) | Экспорт путей из отсортированного дерева. |
| [hadlers_dns_analyze_architecture.md](hadlers_dns_analyze_architecture.md) | DNS content-analysis handlers. |
| [hadlers_host_analyze_architecture.md](hadlers_host_analyze_architecture.md) | Host content-analysis handlers. |
| [hadlers_json_handler_architecture.md](hadlers_json_handler_architecture.md) | Общий JSON helper. |
| [db-architecture.md](db-architecture.md) | SQLAlchemy модели, репозитории и назначение таблиц PostgreSQL Catalog. |
| [stage-two-architecture.md](stage-two-architecture.md) | Stage Two: storage bootstrap, catalog ingestion, parser registry, normalization, quality, traceability. |
| [pipeline-artifacts-and-contracts.md](pipeline-artifacts-and-contracts.md) | Порядок вызова компонентов, входные/выходные артефакты и JSON/Parquet/DB контракты. |
| [extension-points-and-risks.md](extension-points-and-risks.md) | Точки расширения, ограничения, риски и технический долг. |

Примечание: имена файлов `hadlers_*` сохранены из существующей структуры документации. Это опечатка в имени файла, а не имя Python-пакета.
