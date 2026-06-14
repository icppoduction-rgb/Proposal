# Handler: `sort`

## Назначение

`sort` копирует файлы из временных JSON-списков в подготовленное дерево по роли и формату. Это мост между Stage One discovery/filter и content-analysis.

## CLI

| Команда | Класс | Вход | Output root | Summary |
|---|---|---|---|---|
| `python manage.py handlers sort sort-dns-dataset-handler` | `DNSDatasetSortHandler` | `dns-path-file.json`, `dns-file.json` | `PATH_DNS_DATASETS_FILTER` | `sort-dns-format-summary.json` |
| `python manage.py handlers sort sort-host-dataset-handler` | `HostDatasetSortHandler` | `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json` | `PATH_HOST_DATASETS_FILTER` | `sort-host-format-summary.json` |

## Компоненты

| Файл | Назначение |
|---|---|
| `scripts/handlers/sort/router_sort.py` | Маршрутизирует DNS/host sort actions. |
| `scripts/handlers/sort/sort_dns_dataset_handler.py` | Сортирует DNS файлы. |
| `scripts/handlers/sort/sort_host_dataset_handler.py` | Сортирует host файлы. |

## Выходная структура

Sorter формирует дерево вида:

```text
<filter-root>/
  TRAIN/
    csv/
    pcap/
    ...
  VALIDATION/
    ...
  TEST/
    ...
```

Конкретные format buckets определяются логикой sorter по имени/расширению файла. Summary JSON содержит счетчики по ролям и форматам, а также путь к output root.

## JSON summary contract

Фактическая структура summary строится handler-кодом и включает:

| Поле | Назначение |
|---|---|
| `source_path_json` / input path metadata | Из какого temporary JSON читались пути. |
| `output_root` | Корень отсортированного дерева. |
| `roles` / counters | Количество обработанных/скопированных файлов по ролям и форматам. |
| error/skipped counters | Информация о пропущенных файлах, если handler ее сформировал. |

## Место в pipeline

DNS:

```text
analyze_dataset -> sort-dns-dataset-handler -> save-sort-dns-dataset-handler -> dns_analyze
```

Host:

```text
analyze_dataset -> filter_dataset -> sort-host-dataset-handler -> save-sort-host-dataset-handler -> host_analyze
```

## Ограничения

- Sorter работает с файловой системой и может копировать большие объемы данных.
- Он не регистрирует файлы в PostgreSQL Catalog; Stage Two `catalog-ingest` делает отдельное сканирование configured roots.
- Корректность downstream analysis зависит от совпадения format bucket names с action-specific handlers.
