# Архитектура Stage One

Stage One - слой обнаружения, фильтрации, сортировки и первичного анализа файлов датасетов. Он работает в основном с файловой системой и JSON summaries, не пишет normalized Parquet и не регистрирует parser runs.

## CLI entry points

Stage One команды проходят через:

```text
manage.py -> scripts/router_script.py -> scripts/handlers/router_handler.py
```

Типовые группы команд:

```powershell
python manage.py handlers analyze-dataset host-dataset-handler
python manage.py handlers analyze-dataset dns-dataset-handler
python manage.py handlers sort sort-host-dataset-handler
python manage.py handlers sort sort-dns-dataset-handler
python manage.py handlers save-sort save-sort-host-dataset-handler
python manage.py handlers save-sort save-sort-dns-dataset-handler
python manage.py handlers filter-dataset filter-host-dataset-handler
python manage.py handlers host-analyze analyze-auth-log-content
python manage.py handlers dns-analyze analyze-train-csv-content
```

## Handler areas

| Директория | Назначение |
| --- | --- |
| `scripts/handlers/analyze_dataset` | Обход raw DNS/host roots и построение path/file JSON. |
| `scripts/handlers/filter_dataset` | Host-specific фильтрация перед сортировкой. |
| `scripts/handlers/sort` | Раскладка файлов по role/format buckets. |
| `scripts/handlers/save_sort` | Экспорт отсортированных путей в `sort-path-*-file.json`. |
| `scripts/handlers/dns_analyze` | DNS content summaries. |
| `scripts/handlers/host_analyze` | Host content summaries. |
| `scripts/handlers/json_handler` | Общие JSON read/write helpers для handlers. |

## Stage One artifacts

| Artifact | Источник | Назначение |
| --- | --- | --- |
| `dns-path-file.json`, `dns-file.json` | DNS analyze-dataset | Discovery paths/names. |
| `host-path-file.json`, `host-file.json` | Host analyze-dataset | Discovery paths/names. |
| `filter_dataset-host-path-file.json`, `filter_dataset-host-file.json` | Host filter-dataset | Отфильтрованные host paths/names. |
| `sort-dns-format-summary.json`, `sort-host-format-summary.json` | sort handlers | Сводка форматов по sorted tree. |
| `sort-path-dns-file.json`, `sort-path-host-file.json` | save-sort handlers | Пути по role/source_format buckets. |
| `analysis-*-summary.json` | dns/host analyze handlers | Content analysis summaries. |
| Markdown reports | dns/host analyze handlers | Человекочитаемая диагностика. |

`SORT_PATH_DNS_FILE` и `SORT_PATH_HOST_FILE` существуют как backward-compatible aliases в `config.py`. Stage Two может использовать Stage One JSON для диагностики coverage, но production catalog строится через `catalog-ingest`.

## Связь со Stage Two

Stage One не создает `dataset_files`, `parser_runs` или `normalized_artifacts`. Эти сущности создаются Stage Two. Практический порядок такой:

1. Stage One обнаруживает и сортирует raw files.
2. Stage Two `catalog-ingest` сканирует raw/sorted roots и регистрирует catalog rows.
3. `parser-coverage` показывает, какие role/source_format buckets имеют активный parser.
4. `mark-ready` переводит выбранные файлы в `READY_FOR_PARSING`.
5. `normalize-format` или `normalize-all` создают normalized Parquet artifacts.

## Контракты JSON

Stage One JSON contracts простые и в основном dict/list based:

```json
{
  "TRAIN": {
    "csv": ["C:/path/to/file.csv"],
    "pcap": ["C:/path/to/file.pcap"]
  },
  "VALIDATION": {},
  "TEST": {}
}
```

У content-analysis summaries нет единой JSON Schema в коде. Поэтому их нельзя считать стабильным parser input contract для новых Stage Two parser implementations. Для новых парсеров source of truth - `dataset_files.source_format`, parser registry и raw file path/hash.

