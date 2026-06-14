# Handler: `filter_dataset`

## Назначение

`filter_dataset` реализован только для host datasets. Он читает JSON после `analyze_dataset`, применяет whitelist правила к известным группам host-датасетов и создает filtered JSON для сортировки.

## CLI

```powershell
python manage.py handlers filter-dataset filter-host-dataset-handler
```

## Компоненты

| Файл | Назначение |
|---|---|
| `scripts/handlers/filter_dataset/router_filter.py` | Создает `HostDatasetFilterHandler(PATH_TEMP_DATA, PATH_FILTER_LOG)` и вызывает `filter_and_save()`. |
| `scripts/handlers/filter_dataset/filter_host_dataset_handler.py` | Реализует whitelist filtering и запись результата. |

## Входные данные

| Artifact | Где создается | Назначение |
|---|---|---|
| `PATH_TEMP_DATA/host-path-file.json` | `HostDatasetHandler` | Пути host-файлов по ролям. |
| `PATH_TEMP_DATA/host-file.json` | `HostDatasetHandler` | Имена host-файлов по ролям. |

## Выходные данные

| Artifact | Назначение |
|---|---|
| `PATH_TEMP_DATA/filter_dataset-host-path-file.json` | Отфильтрованные пути host-файлов по ролям. |
| `PATH_TEMP_DATA/filter_dataset-host-file.json` | Отфильтрованные имена host-файлов по ролям. |
| filter log | Лог причин исключения/сохранения файлов, путь задается `PATH_FILTER_LOG`. |

## Правила фильтрации

Код содержит allowlist suffix-наборы для известных групп, включая LID-DS, OTRF и Dynamic Malware Analysis. Файлы, не прошедшие правила или не найденные в `host-file.json`, исключаются из downstream sorting.

## Место в pipeline

```text
host analyze_dataset -> filter_dataset -> sort-host-dataset-handler
```

`HostDatasetSortHandler` ожидает именно `filter_dataset-host-path-file.json` и `filter_dataset-host-file.json`. Пропуск этого шага приведет к отсутствию входных JSON для host sort.

## Ограничения и риск

- В `config.py` `PATH_FILTER_LOG` задан с trailing comma и фактически может быть tuple. Router передает это значение напрямую в handler.
- DNS-фильтрация отсутствует.
- Правила фильтрации зашиты в коде; внешнего конфигурационного файла для allowlist нет.
