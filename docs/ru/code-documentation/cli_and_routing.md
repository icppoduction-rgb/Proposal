# CLI и слой routing

## Точка входа

Главная точка входа: `manage.py`.

`manage.py` создает `argparse.ArgumentParser` с позиционными аргументами:

| Аргумент | Назначение |
|---|---|
| `module` | верхний routing namespace: `handlers` или `stage-two` |
| `service` | service/action group внутри module |
| `action` | первый action или первый positional argument service-команды |
| `extra_args` | остаток аргументов для Stage Two команд |

Фактическая маршрутизация:

```text
manage.py
  -> scripts.router_script.router_commands(module, service, action, extra_args)
     -> handlers: scripts.handlers.router_handler.router_commands_handlers(service, action)
     -> stage-two: scripts.stage_two.cli.router_stage_two(service, action, extra_args)
```

Если `module` неизвестен, печатается `config.manage_commands`.

Сверка с кодом от 2026-07-04: `config.manage_commands` является fallback-строкой для вывода в консоль и старше текущего Stage Two router. Для Stage Two используйте `scripts/stage_two/cli.py` и этот документ как актуальный список команд.

## Маршруты Stage One

Файл: `scripts/handlers/router_handler.py`.

| Service | Router | Actions |
|---|---|---|
| `analyze-dataset` | `scripts/handlers/analyze_dataset/router_analyze.py` | `dns-dataset-handler`, `host-dataset-handler` |
| `filter-dataset` | `scripts/handlers/filter_dataset/router_filter.py` | `filter-host-dataset-handler` |
| `sort` | `scripts/handlers/sort/router_sort.py` | `sort-dns-dataset-handler`, `sort-host-dataset-handler` |
| `save-sort` | `scripts/handlers/save_sort/router_save.py` | `save-sort-dns-dataset-handler`, `save-sort-host-dataset-handler` |
| `dns-analyze` | `scripts/handlers/dns_analyze/router_dns.py` | DNS actions по role/format content |
| `host-analyze` | `scripts/handlers/host_analyze/router_host.py` | Host actions по role/format content |

### Порядок Stage One DNS

```bash
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers dns-analyze <action>
```

DNS content actions:

```bash
python manage.py handlers dns-analyze analyze-train-csv-content
python manage.py handlers dns-analyze analyze-train-pcap-content
python manage.py handlers dns-analyze analyze-train-pcap-csv-content
python manage.py handlers dns-analyze analyze-test-csv-content
python manage.py handlers dns-analyze analyze-test-pcap-content
python manage.py handlers dns-analyze analyze-test-pcap-csv-content
python manage.py handlers dns-analyze analyze-validation-pcap-content
python manage.py handlers dns-analyze analyze-validation-txt-content
```

### Порядок Stage One Host

```bash
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers host-analyze <action>
```

Host content actions включают `analyze-csv-content`, `analyze-auth-log-content`, `analyze-json-content`, `analyze-validation-pcapng-content`, `analyze-test-bson-content`, `analyze-test-wls-day-content` и другие actions из `scripts/handlers/host_analyze/router_host.py`.

## Маршруты Stage Two

Файл: `scripts/stage_two/cli.py`.

| Команда | Аргументы | Назначение |
|---|---|---|
| `bootstrap-storage` | нет | создать storage tree под `PATH_DATA_STORAGE` |
| `catalog-ingest` | нет | просканировать `PATH_FOLDER_DATASETS_FILTER` и зарегистрировать файлы |
| `seed-parser-registry` | нет | зарегистрировать normalized schema и parser registry seed |
| `parser-coverage` | `[branch]` | показать coverage catalog formats vs active parsers |
| `mark-ready` | flags или fallback | перевести выбранные файлы в `READY_FOR_PARSING` |
| `normalize-format` | flags или fallback | нормализовать одну группу `branch/role/source_format` |
| `normalize-all` | flags или fallback | нормализовать все ready группы внутри branch по очереди |
| `benchmark-normalization` | flags | измерить скорость одного точного bucket `branch/role/source_format` и оценить throughput |
| `split-large-files` | flags | split line-based больших файлов |
| `normalize-dns` | `[limit]` | legacy branch-level normalization для DNS ready files |
| `normalize-host` | `[limit]` | legacy branch-level normalization для Host ready files |
| `run-duckdb-checks` | нет | создать DuckDB views и analytics report |
| `run-leakage-checks` | нет | проверить model-ready leakage и preprocessing fit role |
| `trace-artifact` | `<model_ready_id_or_artifact_path>` | вывести traceability chain |

### Базовый порядок Stage Two

```bash
python manage.py stage-two bootstrap-storage
python -m alembic -c scripts/db/migrations/alembic.ini upgrade head
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two parser-coverage
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two benchmark-normalization --branch dns --role TRAIN --format csv --limit 1000 --sample-ratio 0.10 --dry-run
python manage.py stage-two normalize-format --branch dns --role TRAIN --format csv --limit 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

Порядок из постановки также поддержан для legacy routes:

```bash
python manage.py stage-two bootstrap-storage
python manage.py stage-two catalog-ingest
python manage.py stage-two seed-parser-registry
python manage.py stage-two normalize-dns 10
python manage.py stage-two normalize-host 10
python manage.py stage-two run-duckdb-checks
python manage.py stage-two run-leakage-checks
python manage.py stage-two trace-artifact <model_ready_id_or_artifact_path>
```

## Аргументы Stage Two

`normalize-dns` и `normalize-host` принимают не более одного optional limit. Значение должно быть неотрицательным integer.

`parser-coverage` принимает optional `branch` из `dns`, `host`, `network`, `hybrid`.

`mark-ready`:

```bash
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --dry-run
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --apply
python manage.py stage-two mark-ready --branch dns --role TRAIN --format csv --retry-failed --apply
python manage.py stage-two mark-ready dry-run:dns:TRAIN:csv
```

`normalize-format`:

```bash
python manage.py stage-two normalize-format \
  --branch host \
  --role TRAIN \
  --format json \
  --limit 100 \
  --workers 1 \
  --batch-size 10000 \
  --max-output-part-rows 50000 \
  --resume \
  --packet-mode packet-summary \
  --hash-output-artifacts
```

Fallback-формат:

```bash
python manage.py stage-two normalize-format host:TRAIN:json:100
```

`normalize-all`:

```bash
python manage.py stage-two normalize-all --branch dns --limit 100 --resume
python manage.py stage-two normalize-all dns:100
```

`split-large-files`:

```bash
python manage.py stage-two split-large-files \
  --branch dns \
  --role TEST \
  --format csv \
  --limit 1 \
  --max-part-size-gb 2 \
  --min-size-gb 1 \
  --header no \
  --apply \
  --register
```

Ограничение: split предназначен для line-based formats. Не применять к binary `cap`, `pcap`, `pcapng`, `bson`.

## Команды и выходы

| Команда | Основной input | Основной output |
|---|---|---|
| `handlers analyze-dataset dns-dataset-handler` | `PATH_DNS_DATASETS` | `PATH_TEMP_DATA/dns-path-file.json`, `dns-file.json` |
| `handlers analyze-dataset host-dataset-handler` | `PATH_HOST_DATASETS` | `host-path-file.json`, `host-file.json` |
| `handlers filter-dataset filter-host-dataset-handler` | Host JSON inventory | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json`, filter log |
| `handlers sort sort-*-dataset-handler` | path/file JSON | sorted tree в `PATH_*_DATASETS_FILTER`, sort summary JSON |
| `handlers save-sort save-sort-*-dataset-handler` | sorted tree | `sort-path-*-file.json`, summary JSON |
| `handlers dns-analyze/host-analyze` | `sort-path-*-file.json` | analysis summary JSON, docs, reports |
| `stage-two catalog-ingest` | `PATH_FOLDER_DATASETS_FILTER` | `datasets`, `ingestion_runs`, `dataset_files` |
| `stage-two seed-parser-registry` | schema JSON + seed JSON | `schema_versions`, `parser_registry` |
| `stage-two normalize-*` | `dataset_files.status=READY_FOR_PARSING` | `parser_runs`, `normalized_artifacts`, Parquet |
| `stage-two run-duckdb-checks` | Parquet layers | JSON quality report, `data_quality_reports` |
| `stage-two run-leakage-checks` | model-ready Parquet + preprocessing catalog | leakage report, `data_quality_reports` |

## Важные ограничения CLI

- `python manage.py stage-two` без команды печатает `unknown Stage Two command` и legacy-текст `config.manage_commands`; этот вывод не содержит все новые команды и не должен считаться полным help.
- `handlers` routes не принимают произвольные flags; `action` должен совпадать с router case.
- Stage One content analysis падает, если нужный role/format bucket отсутствует в `sort-path-*-file.json`.
- `catalog-ingest` сканирует `PATH_FOLDER_DATASETS_FILTER`, а не raw `PATH_FOLDER_DATASETS`.
- `normalize-format` и `normalize-all` обрабатывают только `READY_FOR_PARSING`.
- `benchmark-normalization` использует те же точные bucket-входы, что и `normalize-format`; actual benchmark принудительно включает resume behavior, если не указан `--dry-run`.
- `normalize-all` группирует по `role/source_format` и сохраняет порядок ролей из `ACTIVE_DATASET_ROLE_VALUES`: `TRAIN`, `VALIDATION`, `TEST`.
- `trace-artifact` работает только для уже зарегистрированных `model_ready_artifacts`.
