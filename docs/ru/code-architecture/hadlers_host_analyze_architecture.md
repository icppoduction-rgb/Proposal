# Handler: `host_analyze`

## Назначение

`host_analyze` выполняет анализ содержимого host buckets, подготовленных цепочкой `analyze_dataset -> filter_dataset -> sort -> save_sort`. Каждый action соответствует конкретной роли и формату/типу файла.

## CLI

```powershell
python manage.py handlers host-analyze <action>
```

## Компоненты

| Файл | Назначение |
|---|---|
| `scripts/handlers/host_analyze/router_host.py` | Карта action -> analyzer class. |
| `scripts/handlers/host_analyze/run_action.py` | Общий запуск analyzer и печать результата. |
| `scripts/handlers/host_analyze/analyze_host_*_dataset_handler.py` | Реализации анализа конкретных host buckets. |

## Входные данные

| Artifact | Назначение |
|---|---|
| `PATH_TEMP_DATA/sort-path-host-file.json` | Карта `role -> format -> paths`, созданная `save-sort-host-dataset-handler`. |
| Файлы из sorted tree | Реальное содержимое host файлов, которое анализирует конкретный handler. |

## TRAIN actions

TRAIN actions в router не имеют префикса `train`; role задается внутри соответствующего analyzer.

| Format/scope | Action |
|---|---|
| csv | `analyze-csv-content` |
| auth.log | `analyze-auth-log-content` |
| cpu.log | `analyze-cpu-log-content` |
| diskio.log | `analyze-diskio-log-content` |
| filesystem.log | `analyze-filesystem-log-content` |
| fsstat.log | `analyze-fsstat-log-content` |
| ghc | `analyze-ghc-content` |
| info | `analyze-info-content` |
| journal | `analyze-journal-content` |
| journal~ | `analyze-journal-tilde-content` |
| json | `analyze-json-content` |
| json-1 | `analyze-json-1-content` |
| load.log | `analyze-load-log-content` |
| log | `analyze-log-content` |
| log-1 | `analyze-log-1-content` |
| log-2 | `analyze-log-2-content` |
| log-3 | `analyze-log-3-content` |
| mail.info-1 | `analyze-mail-info-1-content` |
| mail.warn-1 | `analyze-mail-warn-1-content` |
| mainlog | `analyze-mainlog-content` |
| mainlog-1 | `analyze-mainlog-1-content` |
| mainlog-2 | `analyze-mainlog-2-content` |
| mainlog-3 | `analyze-mainlog-3-content` |
| memory.log | `analyze-memory-log-content` |
| messages | `analyze-messages-content` |
| messages-1 | `analyze-messages-1-content` |
| netflow.ids | `analyze-netflow-ids-content` |
| network.log | `analyze-network-log-content` |
| pcap | `analyze-pcap-content` |
| process.log | `analyze-process-log-content` |
| process.summary.log | `analyze-process-summary-log-content` |
| sc | `analyze-sc-content` |
| service.log | `analyze-service-log-content` |
| socket.summary.log | `analyze-socket-summary-log-content` |
| syslog | `analyze-syslog-content` |
| syslog-1 | `analyze-syslog-1-content` |
| syslog-2 | `analyze-syslog-2-content` |
| syslog-3 | `analyze-syslog-3-content` |
| syslog-4 | `analyze-syslog-4-content` |
| syslog.log | `analyze-syslog-log-content` |
| txt | `analyze-txt-content` |
| uptime.log | `analyze-uptime-log-content` |
| xml | `analyze-xml-content` |

## TEST actions

| Format/scope | Action |
|---|---|
| bson | `analyze-test-bson-content` |
| csv | `analyze-test-csv-content` |
| json | `analyze-test-json-content` |
| log | `analyze-test-log-content` |
| netflow_day | `analyze-test-netflow-day-content` |
| txt | `analyze-test-txt-content` |
| wls_day | `analyze-test-wls-day-content` |

## VALIDATION actions

| Format/scope | Action |
|---|---|
| cap | `analyze-validation-cap-content` |
| csv | `analyze-validation-csv-content` |
| json | `analyze-validation-json-content` |
| netflow_day | `analyze-validation-netflow-day-content` |
| pcap | `analyze-validation-pcap-content` |
| pcapng | `analyze-validation-pcapng-content` |
| txt | `analyze-validation-txt-content` |
| wls_day | `analyze-validation-wls-day-content` |

## Выходные данные

Каждый analyzer создает summary JSON в `PATH_TEMP_DATA` и Markdown/текстовые отчеты в docs/report директориях из `config.py`. Имена summary следуют pattern:

```text
analysis-host-<role>-<format>-summary.json
```

Точный набор полей зависит от analyzer, но обычно включает source JSON path, role, format, количество файлов, status, detected columns/fields, sample records, errors/skipped counters и blocking reason.

## Место в pipeline

```text
Host source files
  -> analyze-dataset host-dataset-handler
  -> filter-dataset filter-host-dataset-handler
  -> sort sort-host-dataset-handler
  -> save-sort save-sort-host-dataset-handler
  -> host-analyze <role/format action>
```

`host_analyze` не создает normalized Parquet и не регистрирует PostgreSQL Catalog. Его результаты используются как исследовательская база для реализации Stage Two parsers.

## Связь со Stage Two

Stage One может анализировать больше форматов, чем Stage Two сейчас нормализует. В частности, `netflow_day`, `netflow_ids`, `wls_day` имеют content-analysis handlers, но Stage Two parser registry держит соответствующий host netflow parser inactive/planned, пока parser не реализован.
