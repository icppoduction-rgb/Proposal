# Handler: `analyze_dataset`

## Назначение

`analyze_dataset` выполняет первичный обход исходных директорий DNS и host datasets и формирует временные JSON-списки файлов. Это первый шаг Stage One pipeline.

## CLI

| Команда | Класс | Input root | Output JSON |
|---|---|---|---|
| `python manage.py handlers analyze-dataset dns-dataset-handler` | `DNSDatasetHandler` | `PATH_DNS_DATASETS` | `dns-path-file.json`, `dns-file.json` |
| `python manage.py handlers analyze-dataset host-dataset-handler` | `HostDatasetHandler` | `PATH_HOST_DATASETS` | `host-path-file.json`, `host-file.json` |

## Компоненты

| Файл | Назначение |
|---|---|
| `scripts/handlers/analyze_dataset/router_analyze.py` | Маршрутизирует action на DNS/host handler. |
| `scripts/handlers/analyze_dataset/dns_dataset_handler.py` | Обходит DNS source root. |
| `scripts/handlers/analyze_dataset/host_dataset_handler.py` | Обходит host source root. |

## Контракт выходных JSON

Оба handler создают два файла в `PATH_TEMP_DATA`:

```json
{
  "TRAIN": ["absolute/or/configured/path/to/file"],
  "VALIDATION": ["absolute/or/configured/path/to/file"],
  "TEST": ["absolute/or/configured/path/to/file"]
}
```

`*-path-file.json` содержит пути, `*-file.json` содержит имена файлов. Значения ролей должны быть списками; последующие этапы явно проверяют этот контракт.

## Место в pipeline

```text
analyze_dataset DNS -> sort DNS -> save_sort DNS -> dns_analyze
analyze_dataset host -> filter_dataset host -> sort host -> save_sort host -> host_analyze
```

Для DNS filter step отсутствует. Для host filter step обязателен перед `sort-host-dataset-handler`, потому что sorter читает `filter_dataset-host-*.json`, а не исходные `host-*.json`.

## Ограничения

- Handler не читает содержимое файлов, а строит inventory по файловой системе.
- Роли определяются текущей логикой handler и структурой source root; если структура датасета отличается, последующие этапы могут получить пустые списки.
- JSON создается как временный Stage One artifact и не регистрируется в PostgreSQL Catalog автоматически.
