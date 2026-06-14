# Handler: `save_sort`

## Назначение

`save_sort` обходит уже отсортированное дерево `PATH_*_DATASETS_FILTER` и создает JSON-карту путей, которую используют `dns_analyze` и `host_analyze`.

## CLI

| Команда | Класс | Input root | Output JSON |
|---|---|---|---|
| `python manage.py handlers save-sort save-sort-dns-dataset-handler` | `DNSSortedPathExportHandler` | `PATH_DNS_DATASETS_FILTER` | `sort-path-dns-file.json`, `sort-path-dns-file-summary.json` |
| `python manage.py handlers save-sort save-sort-host-dataset-handler` | `HostSortedPathExportHandler` | `PATH_HOST_DATASETS_FILTER` | `sort-path-host-file.json`, `sort-path-host-file-summary.json` |

## Компоненты

| Файл | Назначение |
|---|---|
| `scripts/handlers/save_sort/router_save.py` | Маршрутизирует DNS/host save-sort actions. |
| `scripts/handlers/save_sort/save_sort_dns_path_handler.py` | Экспортирует DNS sorted paths. |
| `scripts/handlers/save_sort/save_sort_host_path_handler.py` | Экспортирует host sorted paths. |

## Контракт `sort-path-*-file.json`

Файл представляет дерево ролей и форматов:

```json
{
  "TRAIN": {
    "csv": ["path/to/file.csv"],
    "pcap": ["path/to/file.pcap"]
  },
  "VALIDATION": {
    "txt": ["path/to/file.txt"]
  },
  "TEST": {
    "json": ["path/to/file.json"]
  }
}
```

Content-analysis handlers читают этот JSON и выбирают конкретный role/format bucket, соответствующий action.

## Место в pipeline

```text
sort -> save_sort -> dns_analyze / host_analyze
```

`dns_analyze` читает `sort-path-dns-file.json`. `host_analyze` читает `sort-path-host-file.json`.

## Ограничения

- `save_sort` не проверяет содержимое файлов.
- Если sorted tree пустой или bucket отсутствует, downstream content-analysis handler обычно создает summary с blocking status или ошибкой, в зависимости от конкретной реализации.
- JSON path export не заменяет Stage Two catalog ingestion; PostgreSQL Catalog наполняется отдельной командой `stage-two catalog-ingest`.
