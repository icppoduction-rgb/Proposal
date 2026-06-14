# Handler: `dns_analyze`

## Назначение

`dns_analyze` выполняет анализ содержимого DNS buckets, подготовленных цепочкой `analyze_dataset -> sort -> save_sort`. Каждый action соответствует конкретной роли и формату данных.

## CLI

```powershell
python manage.py handlers dns-analyze <action>
```

## Компоненты

| Файл | Назначение |
|---|---|
| `scripts/handlers/dns_analyze/router_dns.py` | Карта action -> analyzer class. |
| `scripts/handlers/dns_analyze/run_action.py` | Общий запуск analyzer и печать результата. |
| `scripts/handlers/dns_analyze/analyze_dns_*_dataset_handler.py` | Реализации анализа конкретных role/format buckets. |

## Входные данные

| Artifact | Назначение |
|---|---|
| `PATH_TEMP_DATA/sort-path-dns-file.json` | Карта `role -> format -> paths`, созданная `save-sort-dns-dataset-handler`. |
| Файлы из sorted tree | Реальное содержимое DNS файлов, которое анализирует конкретный handler. |

## Поддерживаемые actions

| Role | Format/scope | Action | Handler file |
|---|---|---|---|
| TRAIN | csv | `analyze-train-csv-content` | `analyze_dns_train_csv_dataset_handler.py` |
| TRAIN | pcap | `analyze-train-pcap-content` | `analyze_dns_train_pcap_dataset_handler.py` |
| TRAIN | pcap.csv | `analyze-train-pcap-csv-content` | `analyze_dns_train_pcap_csv_dataset_handler.py` |
| TEST | csv | `analyze-test-csv-content` | `analyze_dns_test_csv_dataset_handler.py` |
| TEST | pcap | `analyze-test-pcap-content` | `analyze_dns_test_pcap_dataset_handler.py` |
| TEST | pcap.csv | `analyze-test-pcap-csv-content` | `analyze_dns_test_pcap_csv_dataset_handler.py` |
| VALIDATION | pcap | `analyze-validation-pcap-content` | `analyze_dns_validation_pcap_dataset_handler.py` |
| VALIDATION | txt | `analyze-validation-txt-content` | `analyze_dns_validation_txt_dataset_handler.py` |

## Выходные данные

Каждый analyzer создает summary JSON в `PATH_TEMP_DATA` и Markdown/текстовые отчеты в docs/report директориях из `config.py`. Имена summary follow pattern:

```text
analysis-dns-<role>-<format>-summary.json
```

Примеры:

| Action | Summary |
|---|---|
| `analyze-train-csv-content` | `analysis-dns-train-csv-summary.json` |
| `analyze-test-pcap-content` | `analysis-dns-test-pcap-summary.json` |
| `analyze-validation-txt-content` | `analysis-dns-validation-txt-summary.json` |

Типовой summary содержит source JSON path, role, format, scope/counters, status, detected schema/content information и blocking reason, если анализ невозможен.

## Место в pipeline

```text
DNS source files
  -> analyze-dataset dns-dataset-handler
  -> sort sort-dns-dataset-handler
  -> save-sort save-sort-dns-dataset-handler
  -> dns-analyze <role/format action>
```

`dns_analyze` не записывает PostgreSQL Catalog и не создает normalized Parquet. Его задача - исследовательская/документационная подготовка перед Stage Two parsers.

## Ограничения

- Action должен быть явно зарегистрирован в `router_dns.py`.
- Если `sort-path-dns-file.json` не содержит нужный bucket, конкретный handler может завершить анализ blocking summary.
- Набор DNS content analyzers не равен набору Stage Two parsers. Stage Two активные parser entries определяются `parser_registry_seed.json` и resolver-логикой.
