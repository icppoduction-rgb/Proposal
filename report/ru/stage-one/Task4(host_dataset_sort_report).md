# Отчёт: сортировка Host-датасетов по форматам (этап 4)

## Описание задачи
Реализован этап сортировки отфильтрованных Host-датасетов по форматам файлов.
Обработчик читает `filter-host-file.json` и `filter-host-path-file.json` из `PATH_TEMP_DATA`, определяет формат каждого файла по правилам проекта и формирует структуру директорий внутри `PATH_HOST_DATASETS_FILTER`.

## Какие файлы были добавлены
- `scripts/handlers/sort_host_dataset_handler.py`
- `report/ru/host_dataset_sort_report.md`
- `report/en/host_dataset_sort_report.md`

## Какие файлы были изменены
- `manage.py`

## Команда запуска
- `python manage.py host dataset sort`

`manage.py` остаётся только точкой входа, вся логика сортировки вынесена в `scripts/handlers/sort_host_dataset_handler.py`.

## Описание структуры сортировки
Обработчик гарантированно создаёт разделы:
- `TRAIN`
- `TEST`
- `VALIDATION`
- `EXPERIMENTS`

Внутри каждого раздела создаются папки по форматам, например:

```text
PATH_HOST_DATASETS_FILTER/
  TRAIN/
    csv/
    ghc/
    txt/
    auth.log/
    process.summary.log/
    log-1/
    mainlog-1/
    pcap/
  TEST/
    txt/
    bson/
    json/
    log/
    netflow_day/
    wls_day/
  VALIDATION/
    cap/
    pcap/
    pcapng/
  EXPERIMENTS/
    csv/
    log/
    npz/
```

## Поддерживаемые форматы
Поддерживаются:
- обычные расширения (`csv`, `txt`, `ghc`, `sc`, `json`, `log`, `npz`, `bson`, `pcap`, `pcapng`, `cap`, `xml`, `netflow_ids`);
- смысловые host-логи (`auth.log`, `cpu.log`, `diskio.log`, `filesystem.log`, `fsstat.log`, `load.log`, `memory.log`, `network.log`, `process.log`, `process.summary.log`, `service.log`, `socket.summary.log`, `syslog.log`, `uptime.log`);
- ротационные логи (например, `log.1 -> log-1`, `mainlog.1 -> mainlog-1`);
- файлы `pcap.<timestamp>` (включая `log.pcap.<timestamp>`) -> группа `pcap`;
- нестандартные шаблоны: `messages`, `messages.1`, `journal~`, `netflow_day-*`, `wls_day-*`.

## Логика определения формата
1. Проверяются специальные шаблоны: `netflow_day-*`, `wls_day-*`, `journal~`, `messages`, `mainlog`, ротации (`*.1`, `*.2`, ...), `pcap.<timestamp>`.
2. Для системных логов используется полное смысловое имя (`auth.log`, `process.summary.log` и т.д.), даже если перед именем есть префикс даты/хоста.
3. Для остальных файлов используется расширение.
4. При коллизии имён в целевой папке используется детерминированный hash-суффикс, чтобы не перезаписывать файлы.

## Гарантии безопасности данных
- Оригинальные датасеты не изменяются.
- Файлы не перемещаются и не удаляются.
- Основной режим размещения — hardlink (без дублирования данных и без изменения источника).
- Если hardlink недоступен, используется безопасный fallback на копирование.

## Результат фактического запуска
Результаты сохранены в `PATH_TEMP_DATA/sort-host-format-summary.json`.

Ключевые метрики последнего запуска:
- `created_links_count`: `0`
- `copied_files_count`: `0`
- `skipped_existing_count`: `361646`
- `missing_source_count`: `0`
- `name_mismatch_count`: `0`

Это подтверждает идемпотентность сортировки: при повторном запуске существующая структура переиспользуется без перезаписи и без модификации исходных данных.
