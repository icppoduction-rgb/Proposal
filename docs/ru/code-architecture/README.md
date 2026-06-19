# Архитектура кода

Этот раздел является входной точкой по текущей архитектуре проекта. Он описывает реализованный код, а не планируемую функциональность.

## Общая схема

```text
manage.py
  -> scripts/router_script.py
    -> scripts/handlers/*          Stage One: анализ/сортировка файлов
    -> scripts/stage_two/cli.py     Stage Two: catalog/parser/normalization checks
```

Код построен вокруг двух этапов:

- **Stage One** - файловый discovery/sort/analyze слой, который готовит временные JSON summaries и sorted tree.
- **Stage Two** - catalog-driven слой, который использует filtered tree из `PATH_FOLDER_DATASETS_FILTER`, регистрирует файлы в PostgreSQL, выбирает parsers через registry, пишет normalized Parquet и сохраняет traceability. `PATH_FOLDER_DATASETS` остается immutable raw source root для Stage One и аудита/traceback.

## Документы

| Документ | Назначение |
| --- | --- |
| [general-architecture.md](general-architecture.md) | Общая архитектура, основные слои и сквозной pipeline. |
| [router-architecture.md](router-architecture.md) | `manage.py`, `scripts/router_script.py`, Stage One/Stage Two routing и CLI-совместимость. |
| [stage-one-architecture.md](stage-one-architecture.md) | Stage One pipeline: discovery, filtering, sorting, save-sort, content analysis. |
| [stage-two-architecture.md](stage-two-architecture.md) | Stage Two pipeline: storage bootstrap, catalog ingestion, parser registry, normalization, reports, checks. |
| [db-architecture.md](db-architecture.md) | SQLAlchemy models, repositories, PostgreSQL Catalog tables и session lifecycle. |
| [pipeline-artifacts-and-contracts.md](pipeline-artifacts-and-contracts.md) | Входные/выходные artifacts, JSON/Parquet/DB contracts и порядок команд. |
| [extension-points-and-risks.md](extension-points-and-risks.md) | Точки расширения, parser development flow, ограничения и технический долг. |

Существующие файлы `hadlers_*_architecture.md` оставлены как подробные Stage One handler notes. Опечатка `hadlers` сохранена в именах файлов, чтобы не ломать ссылки.

## Краткий operational flow

```powershell
python manage.py stage-two bootstrap-storage
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two seed-parser-registry
python manage.py stage-two catalog-ingest
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python -m scripts.stage_two.readiness_check
```

Подробное руководство по нормализации находится в [../../ru/normalization/usage_guide.md](../normalization/usage_guide.md).
